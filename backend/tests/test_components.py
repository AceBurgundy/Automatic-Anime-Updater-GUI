from asyncio import run as asyncio_run
from os import utime
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from time import perf_counter, time as current_timestamp
from typing import Any, Dict, List, Optional, Set, Tuple
from unittest import TestCase, main as unittest_main
from unittest.mock import AsyncMock, patch

from httpx import ReadTimeout
from PIL import Image

from config import STALL_TIMEOUT_SECONDS
from constants import (
    DEFAULT_STALL_TIMEOUT_SECONDS,
    MIN_STALL_TIMEOUT_SECONDS,
    MAX_STALL_TIMEOUT_SECONDS,
)

from core.state_manager import StateManager
from core.ai_helper import AIHelper
from core.database import DatabaseManager
from core.reporter import ErrorReporter
from core.scanner import LocalScanner, AnimeFolder
from core.downloader import ResilientDownloader
from core.scraper import AnimepaheScraper
from core.model_manager import ModelManager
from core.safety import SafetyGuard, SafetyViolationError


class TestAnimeRefresherComponents(TestCase):
    """
    Comprehensive unit test suite validating core components of Kyaa Anime Refresher.
    """

    test_dir: Path
    state_file: Path
    temp_download_dir: Path

    def setUp(self) -> None:
        """
        Set up isolated test filesystem directories for testing.

        Returns
        -------
        None
        """
        self.test_dir = Path(mkdtemp())
        self.state_file = self.test_dir / "test_state.json"
        self.temp_download_dir = self.test_dir / "temp"
        self.temp_download_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """
        Clean up temporary test filesystem resources.

        Returns
        -------
        None
        """
        rmtree(self.test_dir, ignore_errors=True)

    # 1. StateManager Tests & Stress Testing
    def test_state_manager_basic_operations(self) -> None:
        """
        Verify viewed count increment, query, and reset in StateManager.

        Returns
        -------
        None
        """
        state_manager: StateManager = StateManager(state_file=self.state_file)
        self.assertEqual(state_manager.get_viewed_count("Test Anime", 1), 0)

        # Test increment
        count_one: int = state_manager.increment_viewed_count("Test Anime", 1)
        self.assertEqual(count_one, 1)
        count_two: int = state_manager.increment_viewed_count("Test Anime", 1)
        self.assertEqual(count_two, 2)

        # Test reset
        state_manager.reset_viewed_count("Test Anime", 1)
        self.assertEqual(state_manager.get_viewed_count("Test Anime", 1), 0)

    def test_state_manager_download_recording(self) -> None:
        """
        Verify recording of downloaded episodes and query deduplication in StateManager.

        Returns
        -------
        None
        """
        state_manager: StateManager = StateManager(state_file=self.state_file)
        self.assertFalse(state_manager.is_episode_downloaded("Solo Leveling", 12))

        state_manager.record_downloaded_episode("Solo Leveling", 12, "Solo Leveling - 12.mp4")
        self.assertTrue(state_manager.is_episode_downloaded("Solo Leveling", 12))
        self.assertEqual(state_manager.get_downloaded_episodes("Solo Leveling"), [12])

        # Duplicate record should not duplicate in list
        state_manager.record_downloaded_episode("Solo Leveling", 12, "Solo Leveling - 12.mp4")
        self.assertEqual(state_manager.get_downloaded_episodes("Solo Leveling"), [12])

        # Add another episode
        state_manager.record_downloaded_episode("Solo Leveling", 13, "Solo Leveling - 13.mp4")
        self.assertEqual(sorted(state_manager.get_downloaded_episodes("Solo Leveling")), [12, 13])

    def test_state_manager_history_and_corruption_recovery(self) -> None:
        """
        Verify history ring buffer capping and recovery from corrupted JSON state files.

        Returns
        -------
        None
        """
        state_manager: StateManager = StateManager(state_file=self.state_file)
        step_index: int
        for step_index in range(60):
            state_manager.record_run(downloaded=step_index, errors=0, notes=f"Run {step_index}")

        # Must be capped at last 50 entries
        self.assertEqual(len(state_manager.data["history"]), 50)
        self.assertEqual(state_manager.data["history"][-1]["downloaded"], 59)

        # Test corrupted JSON recovery
        with open(self.state_file, "w", encoding="utf-8") as file_handle:
            file_handle.write("{ invalid json corrupted content ...")

        state_manager_recovered: StateManager = StateManager(state_file=self.state_file)
        self.assertIn("history", state_manager_recovered.data)
        self.assertEqual(state_manager_recovered.get_viewed_count("Any", 1), 0)

    # 2. AIHelper & Filename Formatting Stress Testing
    def test_ai_helper_diverse_regex_stress(self) -> None:
        """
        Stress test episode number extraction across diverse filename patterns.

        Returns
        -------
        None
        """
        ai_helper: AIHelper = AIHelper()
        test_files: List[str] = [
            "Classroom of the Elite Season 3 - 01.ts",
            "Classroom of the Elite Season 3 - 02.ts",
            "Classroom of the Elite Season 3 - 08.mp4",
            "[SubsPlease] Arifureta Season 3 - 15 (1080p) [ABCD1234].mkv",
            "Show.Name.S02E09.1080p.mkv",
            "Kaiju #8 S2 13.mp4",
            "Sakamoto Days Part 2 12.mp4",
            "Spy x Family Season 3 38.mp4",
            "The Classroom of a Black Cat and a Witch 01.mp4",
            "The Classroom of a Black Cat and a Witch 21.mp4",
            "Show Name - Episode 05 [1080p].mp4",
            "Show Name EP 07.mkv",
            "Show Name 1x14.mp4",
            "Show Name - 001.mp4",
            "Show Name - 100.mp4",
            "Show Name - 1050.mp4",
            "365 Days to the Wedding - 12.mp4",
        ]
        episodes: Set[int] = ai_helper.parse_episode_numbers(test_files)
        expected_episodes: Set[int] = {1, 2, 8, 15, 9, 13, 12, 38, 21, 5, 7, 14, 100, 1050}
        expected_number: int
        for expected_number in expected_episodes:
            self.assertIn(expected_number, episodes, f"Episode {expected_number} failed to be extracted")

    def test_sequential_filename_formatting_patterns(self) -> None:
        """
        Validate sequential filename formatting across diverse naming patterns.

        Returns
        -------
        None
        """
        ai_helper: AIHelper = AIHelper()

        # Pattern 1: Standard hyphen with 2-digit padding
        result_one: str = ai_helper.format_sequential_filename(
            anime_folder_name="Arifureta S3",
            existing_filenames=["Arifureta S3 - 01.ts", "Arifureta S3 - 02.ts"],
            episode_num=16,
            downloaded_ext=".mp4"
        )
        self.assertEqual(result_one, "Arifureta S3 - 16.mp4")

        # Pattern 2: Space without hyphen (e.g. "The Classroom of a Black Cat and a Witch 01.mp4")
        result_two: str = ai_helper.format_sequential_filename(
            anime_folder_name="The Classroom of a Black Cat and a Witch",
            existing_filenames=["The Classroom of a Black Cat and a Witch 01.mp4"],
            episode_num=22,
            downloaded_ext=".mp4"
        )
        self.assertEqual(result_two, "The Classroom of a Black Cat and a Witch 22.mp4")

        # Pattern 3: Release group with bracket tags preserved
        result_three: str = ai_helper.format_sequential_filename(
            anime_folder_name="DanMachi S5",
            existing_filenames=["[SubsPlease] DanMachi S5 - 01 (1080p) [ABCD1234].mkv"],
            episode_num=11,
            downloaded_ext=".mp4"
        )
        self.assertEqual(result_three, "[SubsPlease] DanMachi S5 - 11 (1080p) [ABCD1234].mp4")

        # Pattern 4: 3-digit padding preservation
        result_four: str = ai_helper.format_sequential_filename(
            anime_folder_name="One Piece",
            existing_filenames=["One Piece - 001.mp4"],
            episode_num=2,
            downloaded_ext=".mp4"
        )
        self.assertEqual(result_four, "One Piece - 002.mp4")

        # Pattern 5: Season / Episode (S01E01)
        result_five: str = ai_helper.format_sequential_filename(
            anime_folder_name="Bleach",
            existing_filenames=["Bleach.S01E01.1080p.mkv"],
            episode_num=2,
            downloaded_ext=".mp4"
        )
        self.assertEqual(result_five, "Bleach.S01E02.1080p.mp4")

        # Pattern 6: Empty existing files fallback to default
        result_six: str = ai_helper.format_sequential_filename(
            anime_folder_name="Solo Leveling",
            existing_filenames=[],
            episode_num=1,
            downloaded_ext=".mp4"
        )
        self.assertEqual(result_six, "Solo Leveling - 01.mp4")

    def test_ai_helper_speed_benchmark(self) -> None:
        """
        Benchmark filename formatting throughput across 1,000 sequential iterations.

        Returns
        -------
        None
        """
        ai_helper: AIHelper = AIHelper()
        existing_filenames: List[str] = ["My Hero Academia S7 - 01.mp4"]

        start_time: float = perf_counter()
        iteration_index: int
        for iteration_index in range(1, 1001):
            ai_helper.format_sequential_filename("My Hero Academia S7", existing_filenames, iteration_index, ".mp4")
        elapsed_seconds: float = perf_counter() - start_time

        # 1,000 iterations must take less than 0.15s (ensuring zero external I/O delays)
        self.assertLess(elapsed_seconds, 0.15, f"Formatting benchmark too slow: {elapsed_seconds:.4f}s for 1000 items")

    # 3. Fuzzy Matching & Scraper Logic
    def test_fuzzy_matching(self) -> None:
        """
        Verify fuzzy matching of local folder names against web scraper titles.

        Returns
        -------
        None
        """
        state_manager: StateManager = StateManager(state_file=self.state_file)
        scraper: AnimepaheScraper = AnimepaheScraper(state_manager=state_manager)
        local_folders: List[str] = [
            "365 Days to the Wedding; Kekkon suru tte, Hontou desu ka",
            "Arifureta Shokugyou de Sekai Saikyou Season 3",
            "Classroom of the Elite Season 3",
            "Skeleton Knight in Another World S2",
            "Rich Girl Caretaker I'm Secretly the Caregiver of the Most Popular Girl in This Rich Kid School"
        ]

        match_one: Optional[str] = scraper.match_local_anime("Arifureta Shokugyou de Sekai Saikyou Season 3", local_folders)
        self.assertEqual(match_one, "Arifureta Shokugyou de Sekai Saikyou Season 3")

        match_two: Optional[str] = scraper.match_local_anime("365 Days to the Wedding: Kekkon suru tte, Hontou desu ka?", local_folders)
        self.assertEqual(match_two, "365 Days to the Wedding; Kekkon suru tte, Hontou desu ka")

        match_three: Optional[str] = scraper.match_local_anime("Classroom of the Elite 3rd Season", local_folders)
        self.assertEqual(match_three, "Classroom of the Elite Season 3")

        match_four: Optional[str] = scraper.match_local_anime("Skeleton Knight in Another World II", local_folders)
        self.assertEqual(match_four, "Skeleton Knight in Another World S2")

        match_five: Optional[str] = scraper.match_local_anime("Rich Girl Caretaker: I'm Secretly the Caregiver of the Most Popular Girl in This Rich Kid School", local_folders)
        self.assertEqual(match_five, "Rich Girl Caretaker I'm Secretly the Caregiver of the Most Popular Girl in This Rich Kid School")

    def test_audio_preference_selection_and_fallback(self) -> None:
        """
        Verify sub/dub priority rules, strict filtering, and wait-and-retry threshold fallback.

        Returns
        -------
        None
        """
        state_manager: StateManager = StateManager(state_file=self.state_file)

        sample_options: List[Dict[str, str]] = [
            {"text": "1080p (English)", "href": "http://example.com/1080p-eng"},
            {"text": "720p (English)", "href": "http://example.com/720p-eng"},
            {"text": "1080p (Subbed)", "href": "http://example.com/1080p-sub"},
            {"text": "720p (Subbed)", "href": "http://example.com/720p-sub"}
        ]

        # 1. SUB preference (default 1080p)
        scraper_sub: AnimepaheScraper = AnimepaheScraper(state_manager=state_manager, audio_preference="sub", preferred_resolution="1080")
        option_sub: Optional[Dict[str, str]] = scraper_sub._select_preferred_source(sample_options, "Test Series", 1)
        self.assertIsNotNone(option_sub)
        self.assertEqual(option_sub["href"], "http://example.com/1080p-sub")

        # 2. DUB preference
        scraper_dub: AnimepaheScraper = AnimepaheScraper(state_manager=state_manager, audio_preference="dub", preferred_resolution="1080")
        option_dub: Optional[Dict[str, str]] = scraper_dub._select_preferred_source(sample_options, "Test Series", 1)
        self.assertIsNotNone(option_dub)
        self.assertEqual(option_dub["href"], "http://example.com/1080p-eng")

        # 3. STRICT SUB preference
        dub_only_options: List[Dict[str, str]] = [{"text": "1080p (English)", "href": "http://example.com/1080p-eng"}]
        scraper_strict_sub: AnimepaheScraper = AnimepaheScraper(state_manager=state_manager, audio_preference="sub_strict", preferred_resolution="1080")
        option_strict: Optional[Dict[str, str]] = scraper_strict_sub._select_preferred_source(dub_only_options, "Test Series", 2)
        self.assertIsNone(option_strict)

        # 4. Fallback when 1080p missing (only 720p available)
        options_720_only: List[Dict[str, str]] = [
            {"text": "720p (Subbed)", "href": "http://example.com/720p-sub"},
            {"text": "480p (Subbed)", "href": "http://example.com/480p-sub"}
        ]
        # Runs 1 & 2 skip to wait for 1080p
        option_retry_one: Optional[Dict[str, str]] = scraper_sub._select_preferred_source(options_720_only, "Fallback Anime", 1)
        self.assertIsNone(option_retry_one)
        option_retry_two: Optional[Dict[str, str]] = scraper_sub._select_preferred_source(options_720_only, "Fallback Anime", 1)
        self.assertIsNone(option_retry_two)
        # Run 3 reaches threshold -> falls back to 720p
        option_retry_three: Optional[Dict[str, str]] = scraper_sub._select_preferred_source(options_720_only, "Fallback Anime", 1)
        self.assertIsNotNone(option_retry_three)
        self.assertEqual(option_retry_three["href"], "http://example.com/720p-sub")

    # 5. LocalScanner Directory Scanning
    def test_local_scanner(self) -> None:
        """
        Verify unwatched directory scanning, filtering, and episode metadata parsing.

        Returns
        -------
        None
        """
        anime_dir: Path = self.test_dir / "Anime Unwatched"
        anime_dir.mkdir(parents=True, exist_ok=True)

        # Series 1: standard
        series_folder_one: Path = anime_dir / "Series Alpha"
        series_folder_one.mkdir()
        (series_folder_one / "Series Alpha - 01.mp4").write_bytes(b"video1")
        (series_folder_one / "Series Alpha - 02.mp4").write_bytes(b"video2")

        # Series 2: space delimited
        series_folder_two: Path = anime_dir / "Series Beta"
        series_folder_two.mkdir()
        (series_folder_two / "Series Beta 01.mkv").write_bytes(b"video1")
        (series_folder_two / "Series Beta 02.mkv").write_bytes(b"video2")
        (series_folder_two / "Series Beta 03.mkv").write_bytes(b"video3")
        (series_folder_two / "extra.txt").write_bytes(b"text file")

        # Hidden / Temp folder (must be ignored)
        series_hidden: Path = anime_dir / ".hidden_folder"
        series_hidden.mkdir()
        (series_hidden / "ignored.mp4").write_bytes(b"ignored")

        scanner: LocalScanner = LocalScanner(target_dir=anime_dir)
        scanned: List[AnimeFolder] = scanner.scan_unwatched()

        self.assertEqual(len(scanned), 2)
        names: Set[str] = {folder_item.name for folder_item in scanned}
        self.assertEqual(names, {"Series Alpha", "Series Beta"})

        beta_obj: AnimeFolder = next(folder_item for folder_item in scanned if folder_item.name == "Series Beta")
        self.assertEqual(beta_obj.episode_numbers, {1, 2, 3})
        self.assertEqual(len(beta_obj.video_files), 3)

    # 6. SafetyGuard Verification
    def test_safety_guard_violations(self) -> None:
        """
        Verify that SafetyGuard blocks writes to existing files and permits writes to new files.

        Returns
        -------
        None
        """
        guard: SafetyGuard = SafetyGuard(snapshot_path=Path("nonexistent_snapshot.json"))

        # Test 1: Writing to an existing file should raise SafetyViolationError
        existing_file: Path = self.test_dir / "existing_file.mp4"
        existing_file.write_bytes(b"data")

        with self.assertRaises(SafetyViolationError):
            guard.verify_write_safety(existing_file)

        # Test 2: Writing to a new nonexistent file should succeed
        new_file: Path = self.test_dir / "completely_new_file.mp4"
        guard.verify_write_safety(new_file)  # Should not raise

    def test_ai_helper_is_title_match(self) -> None:
        """
        Verify title equivalence matching and symbol stripping rules in AIHelper.

        Returns
        -------
        None
        """
        ai_helper: AIHelper = AIHelper()
        # Fast path exact and season normalization
        self.assertTrue(ai_helper.is_title_match("Solo Leveling", "Solo Leveling"))
        self.assertTrue(ai_helper.is_title_match("Solo Leveling", "solo leveling"))
        self.assertTrue(ai_helper.is_title_match("Arifureta S3", "Arifureta Season 3"))
        self.assertTrue(ai_helper.is_title_match("Classroom of the Elite 3rd Season", "Classroom of the Elite Season 3"))
        self.assertTrue(ai_helper.is_title_match("365 Days to the Wedding: Kekkon", "365 Days to the Wedding; Kekkon"))

        # Windows FS symbol-stripping: folder name is missing forbidden chars that are in the real title
        # Colon dropped: "Mecha-Ude: Mechanical Arms" -> folder "Mecha-Ude Mechanical Arms"
        self.assertTrue(ai_helper.is_title_match("Mecha-Ude Mechanical Arms", "Mecha-Ude: Mechanical Arms"))
        # Colon dropped: subtitle separator
        self.assertTrue(ai_helper.is_title_match("Re Zero Starting Life in Another World", "Re:Zero - Starting Life in Another World"))
        # Asterisks dropped: "Watari-kun's ****** Is About to Collapse"
        self.assertTrue(ai_helper.is_title_match("Watari-kun's  Is About to Collapse", "Watari-kun's ****** Is About to Collapse"))
        # Slash dropped: "Sword Art Online: Alicization - War of Underworld"
        self.assertTrue(ai_helper.is_title_match("Sword Art Online Alicization War of Underworld", "Sword Art Online: Alicization - War of Underworld"))
        # Question mark dropped: "Is It Wrong to Try to Pick Up Girls in a Dungeon?"
        self.assertTrue(ai_helper.is_title_match("Is It Wrong to Try to Pick Up Girls in a Dungeon", "Is It Wrong to Try to Pick Up Girls in a Dungeon?"))

        # Distinct franchises without AI server running should return False (safe default)
        self.assertFalse(ai_helper.is_title_match("Grandblue S3", "Granblue Fantasy: The Animation"))
        self.assertFalse(ai_helper.is_title_match("Naruto Shippuden", "Bleach"))
        self.assertFalse(ai_helper.is_title_match("", "Solo Leveling"))

    def test_closest_resolution_priority_routing(self) -> None:
        """
        Verify closest-resolution fallback routing rules across retry iterations.

        Returns
        -------
        None
        """
        state_manager: StateManager = StateManager(state_file=self.state_file)
        scraper: AnimepaheScraper = AnimepaheScraper(state_manager=state_manager)

        options: List[Dict[str, str]] = [
            {"text": "1080p (Subbed)", "href": "http://example.com/1080p"},
            {"text": "360p (Subbed)", "href": "http://example.com/360p"}
        ]

        # 1. Target 720p (missing 720p) -> After 3 retries, picks 1080p (next highest)
        # Runs 1 and 2 should return None (Wait & Retry)
        result_retry_one: Optional[Dict[str, str]] = scraper._select_preferred_source(options, "Test Anime 720", 1, preferred_resolution="720")
        self.assertIsNone(result_retry_one)
        result_retry_two: Optional[Dict[str, str]] = scraper._select_preferred_source(options, "Test Anime 720", 1, preferred_resolution="720")
        self.assertIsNone(result_retry_two)
        # Run 3 reaches threshold -> falls back to next highest (1080p)
        result_retry_three: Optional[Dict[str, str]] = scraper._select_preferred_source(options, "Test Anime 720", 1, preferred_resolution="720")
        self.assertIsNotNone(result_retry_three)
        self.assertEqual(result_retry_three["href"], "http://example.com/1080p")

        # 2. Target 1080p (missing 1080p) -> After 3 retries, picks next lowest (720p)
        lower_options: List[Dict[str, str]] = [
            {"text": "720p (Subbed)", "href": "http://example.com/720p"},
            {"text": "480p (Subbed)", "href": "http://example.com/480p"}
        ]
        scraper._select_preferred_source(lower_options, "Test Anime 1080", 1, preferred_resolution="1080")
        scraper._select_preferred_source(lower_options, "Test Anime 1080", 1, preferred_resolution="1080")
        result_1080_retry_three: Optional[Dict[str, str]] = scraper._select_preferred_source(lower_options, "Test Anime 1080", 1, preferred_resolution="1080")
        self.assertIsNotNone(result_1080_retry_three)
        self.assertEqual(result_1080_retry_three["href"], "http://example.com/720p")

        # 3. Exact match on run 1 -> immediate return
        exact_result: Optional[Dict[str, str]] = scraper._select_preferred_source(options, "Test Anime Exact", 2, preferred_resolution="1080")
        self.assertIsNotNone(exact_result)
        self.assertEqual(exact_result["href"], "http://example.com/1080p")

    def test_error_report_file_formatting(self) -> None:
        """
        Verify error report formatting and write verification by SafetyGuard.

        Returns
        -------
        None
        """
        error_report_path: Path = self.test_dir / "error.txt"

        entries: List[str] = [
            "The anime folder named \"GrandBlue S3\" was searched and the first result returned was \"Granblue Fantasy\" which we consider different and skipped this anime. Search for \"GrandBlue S3\" gave \"Granblue Fantasy\" as its first result which is not the same anime. Please rename the folder to the anime's proper name based on the website to ensure it gets searched properly.",
            "The anime folder named \"Unknown Anime XYZ\" was searched and no results were found on the website. Please check the spelling or rename the folder to the anime's official name."
        ]

        # Write with single blank line separation (double newline)
        report_text: str = "\n\n".join(entries) + "\n"
        with open(error_report_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(report_text)

        self.assertTrue(error_report_path.exists())
        with open(error_report_path, "r", encoding="utf-8") as file_handle:
            content: str = file_handle.read()

        self.assertIn("GrandBlue S3", content)
        self.assertIn("Unknown Anime XYZ", content)
        self.assertIn("\n\nThe anime folder named \"Unknown Anime XYZ\"", content)

        # Verify safety guard permits error.txt
        guard: SafetyGuard = SafetyGuard(snapshot_path=Path("nonexistent_snapshot.json"))
        guard.verify_write_safety(error_report_path)  # Should not raise

    def test_local_scanner_ignored(self) -> None:
        """
        Verify that ignored folders and files are filtered out during local scan.

        Returns
        -------
        None
        """
        anime_dir: Path = self.test_dir / "Anime Unwatched"
        anime_dir.mkdir(parents=True, exist_ok=True)

        # Folder 1: Normal folder
        series_folder_one: Path = anime_dir / "Solo Leveling"
        series_folder_one.mkdir()
        (series_folder_one / "Solo Leveling - 01.mp4").write_bytes(b"vid1")
        (series_folder_one / "Solo Leveling - 02.mp4").write_bytes(b"vid2")

        # Folder 2: Ignored folder "another one"
        series_folder_two: Path = anime_dir / "another one"
        series_folder_two.mkdir()
        (series_folder_two / "another one - 01.mp4").write_bytes(b"vid1")

        # Folder 3: Folder with ignored file "others.txt" and "sample.mp4"
        series_folder_three: Path = anime_dir / "Bleach"
        series_folder_three.mkdir()
        (series_folder_three / "Bleach - 01.mp4").write_bytes(b"vid1")
        (series_folder_three / "Bleach - 02.mp4").write_bytes(b"vid2")
        (series_folder_three / "sample.mp4").write_bytes(b"ignored_vid")
        (series_folder_three / "others.txt").write_bytes(b"txt")

        # Standalone file in root: others.txt
        (anime_dir / "others.txt").write_bytes(b"root text")

        # Scanner with ignored: ['others.txt, "another one"', 'sample.mp4']
        ignored_patterns: List[str] = ['others.txt, "another one"', 'sample.mp4']
        scanner: LocalScanner = LocalScanner(target_dir=anime_dir, ignored=ignored_patterns)
        scanned_folders: List[AnimeFolder] = scanner.scan_unwatched()

        # "another one" must be completely ignored
        folder_names: Set[str] = {folder.name for folder in scanned_folders}
        self.assertIn("Solo Leveling", folder_names)
        self.assertIn("Bleach", folder_names)
        self.assertNotIn("another one", folder_names)
        self.assertEqual(len(scanned_folders), 2)

        # Bleach should only have 2 video files (sample.mp4 ignored)
        bleach_object: AnimeFolder = next(folder for folder in scanned_folders if folder.name == "Bleach")
        self.assertEqual(len(bleach_object.video_files), 2)
        bleach_file_names: Set[str] = {video_file.name for video_file in bleach_object.video_files}
        self.assertNotIn("sample.mp4", bleach_file_names)
        self.assertNotIn("others.txt", bleach_file_names)

    def test_database_manager_crud_and_migration(self) -> None:
        """
        Verify CRUD operations, settings storage, and migration logic in DatabaseManager.

        Returns
        -------
        None
        """
        database_file: Path = self.test_dir / "test_refresher.db"
        database_manager: DatabaseManager = DatabaseManager(database_file)

        # 1. Settings
        database_manager.set_setting("test_key", "test_val")
        self.assertEqual(database_manager.get_setting("test_key"), "test_val")
        database_manager.set_bool_setting("folder_as_title", True)
        self.assertTrue(database_manager.get_bool_setting("folder_as_title"))
        database_manager.set_bool_setting("folder_as_title", False)
        self.assertFalse(database_manager.get_bool_setting("folder_as_title"))

        # 2. Ignored items
        database_manager.add_ignored_items(["Others", "another folder", "clip.mp4"])
        ignored_items: List[str] = database_manager.get_ignored_items()
        self.assertIn("Others", ignored_items)
        self.assertIn("another folder", ignored_items)
        self.assertIn("clip.mp4", ignored_items)

        removed_items: List[str] = database_manager.remove_ignored_items(["others", "nonexistent"])
        self.assertEqual(removed_items, ["Others"])
        self.assertNotIn("Others", database_manager.get_ignored_items())

        database_manager.clear_ignored_items()
        self.assertEqual(len(database_manager.get_ignored_items()), 0)

        # 3. Series upsert & mapping cache
        series_folder_path: Path = self.test_dir / "Solo Leveling"
        series_identifier: int = database_manager.upsert_series(
            folder_path=series_folder_path,
            folder_name="Solo Leveling",
            site_title="Solo Leveling",
            site_session="a8f9c12345"
        )
        self.assertIsInstance(series_identifier, int)
        series_record: Optional[Dict[str, Any]] = database_manager.get_series_by_folder_path(series_folder_path)
        self.assertIsNotNone(series_record)
        self.assertEqual(series_record["site_session"], "a8f9c12345")
        self.assertEqual(series_record["site_title"], "Solo Leveling")

        # 4. Downloaded episodes
        database_manager.record_downloaded_episode(series_identifier, 1, "Solo Leveling 01.mp4", "1080p", "sub")
        database_manager.record_downloaded_episode(series_identifier, 2, "Solo Leveling 02.mp4", "1080p", "sub")
        downloaded_episodes: Set[int] = database_manager.get_downloaded_episodes_for_series(series_identifier)
        self.assertEqual(downloaded_episodes, {1, 2})
        self.assertTrue(database_manager.is_episode_downloaded(series_identifier, 1))
        self.assertFalse(database_manager.is_episode_downloaded(series_identifier, 3))

        # 5. History
        database_manager.record_run_history(downloaded_count=2, error_count=0, notes="Test Run")
        # Check history recorded without exception

    def test_ai_helper_folder_indexed_filename(self) -> None:
        """
        Verify folder-indexed sequential filename formatting and digit padding detection.

        Returns
        -------
        None
        """
        ai_helper: AIHelper = AIHelper()
        # Default 2-digit padding
        filename_one: str = ai_helper.format_folder_indexed_filename("Solo Leveling", 1)
        self.assertEqual(filename_one, "Solo Leveling 01.mp4")
        filename_twelve: str = ai_helper.format_folder_indexed_filename("Solo Leveling", 12)
        self.assertEqual(filename_twelve, "Solo Leveling 12.mp4")

        # 3-digit padding when existing files have 3 digits
        existing_filenames_three: List[str] = ["One Piece 001.mp4", "One Piece 002.mp4"]
        filename_three: str = ai_helper.format_folder_indexed_filename(
            "One Piece", 5, existing_filenames=existing_filenames_three
        )
        self.assertEqual(filename_three, "One Piece 005.mp4")

    def test_ai_helper_decompose_queries_and_candidate_ranking(self) -> None:
        """
        Verify search query decomposition and candidate ranking heuristics.

        Returns
        -------
        None
        """
        ai_helper: AIHelper = AIHelper()

        # Test DanMachi IV query decomposition
        queries: List[str] = ai_helper.decompose_search_queries("Is It Wrong to Try to Pick Up Girls in a Dungeon IV")
        self.assertIn("Is It Wrong to Try to Pick Up Girls in a Dungeon IV", queries)
        self.assertIn("Is It Wrong to Try to Pick Up Girls in a Dungeon", queries)

        # Test candidate ranking with multiple search results
        # User folder: "Trapped in a Dating Sim The World of Otome Games is Tough for Mobs 2"
        # Candidate 1: "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs" (Season 1)
        # Candidate 2: "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs 2nd Season" (Season 2)
        # Candidate 3: "Dating Sim Something Else"
        candidates: List[Dict[str, str]] = [
            {"title": "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs", "session": "s1_session"},
            {"title": "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs 2nd Season", "session": "s2_session"},
            {"title": "Dating Sim Something Else", "session": "s3_session"}
        ]
        best_candidate: Optional[Dict[str, Any]]
        best_score: float
        best_candidate, best_score, _, _ = ai_helper.rank_and_score_candidates(
            folder_title="Trapped in a Dating Sim The World of Otome Games is Tough for Mobs 2",
            candidates=candidates,
            threshold=0.75
        )
        self.assertIsNotNone(best_candidate)
        self.assertEqual(best_candidate["session"], "s2_session")
        self.assertGreaterEqual(best_score, 0.85)

    def test_error_reporter_html_generation(self) -> None:
        """
        Verify HTML error report formatting and generation.

        Returns
        -------
        None
        """
        reporter: ErrorReporter = ErrorReporter()
        self.assertFalse(reporter.has_errors())

        reporter.add_title_mismatch_error(
            folder_name="DanMachi IV",
            search_query="DanMachi IV",
            closest_candidate="Dungeon ni Deai IV",
            similarity_score=0.92
        )
        reporter.add_generic_error(
            folder_name="Broken Anime",
            error_type="download_failed",
            message="Connection closed by peer"
        )
        self.assertTrue(reporter.has_errors())

        html_path: Path = self.test_dir / "errors.html"
        generation_success: bool = reporter.write_html_report(html_path)
        self.assertTrue(generation_success)
        self.assertTrue(html_path.exists())

        html_content: str = html_path.read_text(encoding="utf-8")
        self.assertIn("DanMachi IV", html_content)
        self.assertIn("Dungeon ni Deai IV", html_content)
        self.assertIn("Broken Anime", html_content)
        self.assertIn("ERRORS_DATA", html_content)

    def test_downloader_touch_folder_metadata(self) -> None:
        """
        Verify folder modification timestamp updates after successful downloads.

        Returns
        -------
        None
        """
        downloader: ResilientDownloader = ResilientDownloader(temp_dir=self.temp_download_dir)
        anime_directory: Path = self.test_dir / "Anime Folder To Touch"
        anime_directory.mkdir(parents=True, exist_ok=True)

        # Set old timestamp
        old_timestamp: float = current_timestamp() - 10000
        utime(str(anime_directory), (old_timestamp, old_timestamp))
        self.assertLess(anime_directory.stat().st_mtime, current_timestamp() - 5000)

        # Touch metadata
        touch_success: bool = downloader.touch_folder_metadata(anime_directory)
        self.assertTrue(touch_success)
        # Should now be current time
        self.assertAlmostEqual(anime_directory.stat().st_mtime, current_timestamp(), delta=5.0)

    def test_scanner_and_folder_limiting(self) -> None:
        """
        Verify scanner discovery and slicing behavior for batch limit execution.

        Returns
        -------
        None
        """
        # Create 10 dummy anime folders
        base_directory: Path = self.test_dir / "Anime Unwatched Test"
        base_directory.mkdir(parents=True, exist_ok=True)
        for folder_index in range(1, 11):
            anime_folder_path: Path = base_directory / f"Anime Series {folder_index:02d}"
            anime_folder_path.mkdir(parents=True, exist_ok=True)
            (anime_folder_path / f"Anime Series {folder_index:02d} 01.mp4").write_text("dummy", encoding="utf-8")

        scanner: LocalScanner = LocalScanner(target_dir=base_directory)
        all_folders: List[AnimeFolder] = scanner.scan_unwatched()
        self.assertEqual(len(all_folders), 10)

        # Apply limit to 5 folders
        limited_five_folders: List[AnimeFolder] = all_folders[:5]
        self.assertEqual(len(limited_five_folders), 5)
        self.assertEqual(limited_five_folders[0].name, "Anime Series 01")
        self.assertEqual(limited_five_folders[4].name, "Anime Series 05")

    def test_scraper_mirror_rotation(self) -> None:
        """
        Verify round-robin fallback mirror rotation in AnimepaheScraper.

        Returns
        -------
        None
        """
        state_manager: StateManager = StateManager(state_file=self.state_file)
        mirrors: List[str] = [
            "https://animepahe.pw",
            "https://animepahe.org",
            "https://animepahe.com",
            "https://animepahe.ru"
        ]
        scraper: AnimepaheScraper = AnimepaheScraper(state_manager=state_manager, base_urls=mirrors)
        self.assertEqual(scraper.active_base_url, "https://animepahe.pw")

        # Mock async browser methods to avoid starting real browser
        scraper._reset_browser_context = AsyncMock()
        scraper._safe_goto = AsyncMock(return_value=(None, None))
        scraper._handle_cloudflare_if_present = AsyncMock(return_value=True)

        async def run_rotation_test() -> None:
            """
            Execute mirror rotation assertions asynchronously.

            Returns
            -------
            None
            """
            mirror_one: str = await scraper.rotate_mirror()
            self.assertEqual(mirror_one, "https://animepahe.org")
            mirror_two: str = await scraper.rotate_mirror()
            self.assertEqual(mirror_two, "https://animepahe.com")
            mirror_three: str = await scraper.rotate_mirror()
            self.assertEqual(mirror_three, "https://animepahe.ru")
            mirror_four: str = await scraper.rotate_mirror()
            self.assertEqual(mirror_four, "https://animepahe.pw")

        asyncio_run(run_rotation_test())

    def test_stall_timeout_configuration(self) -> None:
        """
        Verify that stall timeout constants and environment configuration fall within bounds.

        Returns
        -------
        None
        """
        self.assertEqual(DEFAULT_STALL_TIMEOUT_SECONDS, 45)
        self.assertEqual(MIN_STALL_TIMEOUT_SECONDS, 30)
        self.assertEqual(MAX_STALL_TIMEOUT_SECONDS, 60)
        self.assertGreaterEqual(STALL_TIMEOUT_SECONDS, 30)
        self.assertLessEqual(STALL_TIMEOUT_SECONDS, 60)

    def test_resilient_downloader_stall_watchdog(self) -> None:
        """
        Verify that ResilientDownloader cleanly handles stream stalls and purges partial files.

        Returns
        -------
        None
        """
        downloader: ResilientDownloader = ResilientDownloader(temp_dir=self.temp_download_dir)
        target_directory: Path = self.test_dir / "target"
        target_directory.mkdir(parents=True, exist_ok=True)
        filename: str = "Stalled_Download - 01.mp4"

        with patch("httpx.Client.stream") as mock_stream:
            mock_stream.side_effect = ReadTimeout("Inactivity timeout: 0 bytes received")
            result: bool = downloader.download_file(
                url="https://cdn.example.com/stalled.mp4",
                target_dir=target_directory,
                final_filename=filename,
                stall_timeout=1.0,
            )
            self.assertFalse(result)
            partial_path: Path = downloader.get_temp_path(filename)
            self.assertFalse(partial_path.exists())
            self.assertFalse((target_directory / filename).exists())


if __name__ == "__main__":
    unittest_main()


