import io
import json
import time
import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image

from core.state_manager import StateManager
from core.ai_helper import AIHelper
from core.database import DatabaseManager
from core.reporter import ErrorReporter
from core.scanner import LocalScanner, AnimeFolder
from core.downloader import ResilientDownloader
from core.scraper import AnimepaheScraper
from core.model_manager import ModelManager
from core.safety import SafetyGuard, SafetyViolationError


class TestAnimeRefresherComponents(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.state_file = self.test_dir / "test_state.json"
        self.temp_download_dir = self.test_dir / "temp"
        self.temp_download_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # =========================================================================
    # 1. StateManager Tests & Stress Testing
    # =========================================================================
    def test_state_manager_basic_operations(self):
        sm = StateManager(state_file=self.state_file)
        self.assertEqual(sm.get_viewed_count("Test Anime", 1), 0)
        
        # Test increment
        c1 = sm.increment_viewed_count("Test Anime", 1)
        self.assertEqual(c1, 1)
        c2 = sm.increment_viewed_count("Test Anime", 1)
        self.assertEqual(c2, 2)
        
        # Test reset
        sm.reset_viewed_count("Test Anime", 1)
        self.assertEqual(sm.get_viewed_count("Test Anime", 1), 0)

    def test_state_manager_download_recording(self):
        sm = StateManager(state_file=self.state_file)
        self.assertFalse(sm.is_episode_downloaded("Solo Leveling", 12))
        
        sm.record_downloaded_episode("Solo Leveling", 12, "Solo Leveling - 12.mp4")
        self.assertTrue(sm.is_episode_downloaded("Solo Leveling", 12))
        self.assertEqual(sm.get_downloaded_episodes("Solo Leveling"), [12])
        
        # Duplicate record should not duplicate in list
        sm.record_downloaded_episode("Solo Leveling", 12, "Solo Leveling - 12.mp4")
        self.assertEqual(sm.get_downloaded_episodes("Solo Leveling"), [12])
        
        # Add another episode
        sm.record_downloaded_episode("Solo Leveling", 13, "Solo Leveling - 13.mp4")
        self.assertEqual(sorted(sm.get_downloaded_episodes("Solo Leveling")), [12, 13])

    def test_state_manager_history_and_corruption_recovery(self):
        sm = StateManager(state_file=self.state_file)
        for i in range(60):
            sm.record_run(downloaded=i, errors=0, notes=f"Run {i}")
        
        # Must be capped at last 50 entries
        self.assertEqual(len(sm.data["history"]), 50)
        self.assertEqual(sm.data["history"][-1]["downloaded"], 59)

        # Test corrupted JSON recovery
        with open(self.state_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json corrupted content ...")
        
        sm_recovered = StateManager(state_file=self.state_file)
        self.assertIn("history", sm_recovered.data)
        self.assertEqual(sm_recovered.get_viewed_count("Any", 1), 0)

    # =========================================================================
    # 2. AIHelper & Filename Formatting Stress Testing
    # =========================================================================
    def test_ai_helper_diverse_regex_stress(self):
        ai = AIHelper()
        test_files = [
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
        episodes = ai.parse_episode_numbers(test_files)
        expected = {1, 2, 8, 15, 9, 13, 12, 38, 21, 5, 7, 14, 100, 1050}
        for exp in expected:
            self.assertIn(exp, episodes, f"Episode {exp} failed to be extracted")

    def test_sequential_filename_formatting_patterns(self):
        ai = AIHelper()
        
        # Pattern 1: Standard hyphen with 2-digit padding
        res1 = ai.format_sequential_filename(
            anime_folder_name="Arifureta S3",
            existing_filenames=["Arifureta S3 - 01.ts", "Arifureta S3 - 02.ts"],
            episode_num=16,
            downloaded_ext=".mp4"
        )
        self.assertEqual(res1, "Arifureta S3 - 16.mp4")

        # Pattern 2: Space without hyphen (e.g. "The Classroom of a Black Cat and a Witch 01.mp4")
        res2 = ai.format_sequential_filename(
            anime_folder_name="The Classroom of a Black Cat and a Witch",
            existing_filenames=["The Classroom of a Black Cat and a Witch 01.mp4"],
            episode_num=22,
            downloaded_ext=".mp4"
        )
        self.assertEqual(res2, "The Classroom of a Black Cat and a Witch 22.mp4")

        # Pattern 3: Release group with bracket tags preserved
        res3 = ai.format_sequential_filename(
            anime_folder_name="DanMachi S5",
            existing_filenames=["[SubsPlease] DanMachi S5 - 01 (1080p) [ABCD1234].mkv"],
            episode_num=11,
            downloaded_ext=".mp4"
        )
        self.assertEqual(res3, "[SubsPlease] DanMachi S5 - 11 (1080p) [ABCD1234].mp4")

        # Pattern 4: 3-digit padding preservation
        res4 = ai.format_sequential_filename(
            anime_folder_name="One Piece",
            existing_filenames=["One Piece - 001.mp4"],
            episode_num=2,
            downloaded_ext=".mp4"
        )
        self.assertEqual(res4, "One Piece - 002.mp4")

        # Pattern 5: Season / Episode (S01E01)
        res5 = ai.format_sequential_filename(
            anime_folder_name="Bleach",
            existing_filenames=["Bleach.S01E01.1080p.mkv"],
            episode_num=2,
            downloaded_ext=".mp4"
        )
        self.assertEqual(res5, "Bleach.S01E02.1080p.mp4")

        # Pattern 6: Empty existing files fallback to default
        res6 = ai.format_sequential_filename(
            anime_folder_name="Solo Leveling",
            existing_filenames=[],
            episode_num=1,
            downloaded_ext=".mp4"
        )
        self.assertEqual(res6, "Solo Leveling - 01.mp4")

    def test_ai_helper_speed_benchmark(self):
        ai = AIHelper()
        existing = ["My Hero Academia S7 - 01.mp4"]
        
        start = time.perf_counter()
        for i in range(1, 1001):
            _ = ai.format_sequential_filename("My Hero Academia S7", existing, i, ".mp4")
        elapsed = time.perf_counter() - start
        
        # 1,000 iterations must take less than 0.15s (ensuring zero external I/O delays)
        self.assertLess(elapsed, 0.15, f"Formatting benchmark too slow: {elapsed:.4f}s for 1000 items")

    # =========================================================================
    # 3. Fuzzy Matching & Scraper Logic
    # =========================================================================
    def test_fuzzy_matching(self):
        sm = StateManager(state_file=self.state_file)
        scraper = AnimepaheScraper(state_manager=sm)
        local_folders = [
            "365 Days to the Wedding; Kekkon suru tte, Hontou desu ka",
            "Arifureta Shokugyou de Sekai Saikyou Season 3",
            "Classroom of the Elite Season 3",
            "Skeleton Knight in Another World S2",
            "Rich Girl Caretaker I'm Secretly the Caregiver of the Most Popular Girl in This Rich Kid School"
        ]
        
        match1 = scraper.match_local_anime("Arifureta Shokugyou de Sekai Saikyou Season 3", local_folders)
        self.assertEqual(match1, "Arifureta Shokugyou de Sekai Saikyou Season 3")

        match2 = scraper.match_local_anime("365 Days to the Wedding: Kekkon suru tte, Hontou desu ka?", local_folders)
        self.assertEqual(match2, "365 Days to the Wedding; Kekkon suru tte, Hontou desu ka")

        match3 = scraper.match_local_anime("Classroom of the Elite 3rd Season", local_folders)
        self.assertEqual(match3, "Classroom of the Elite Season 3")

        match4 = scraper.match_local_anime("Skeleton Knight in Another World II", local_folders)
        self.assertEqual(match4, "Skeleton Knight in Another World S2")

        match5 = scraper.match_local_anime("Rich Girl Caretaker: I'm Secretly the Caregiver of the Most Popular Girl in This Rich Kid School", local_folders)
        self.assertEqual(match5, "Rich Girl Caretaker I'm Secretly the Caregiver of the Most Popular Girl in This Rich Kid School")

    def test_audio_preference_selection_and_fallback(self):
        sm = StateManager(state_file=self.state_file)
        
        sample_options = [
            {"text": "1080p (English)", "href": "http://example.com/1080p-eng"},
            {"text": "720p (English)", "href": "http://example.com/720p-eng"},
            {"text": "1080p (Subbed)", "href": "http://example.com/1080p-sub"},
            {"text": "720p (Subbed)", "href": "http://example.com/720p-sub"}
        ]

        # 1. SUB preference (default 1080p)
        scraper_sub = AnimepaheScraper(state_manager=sm, audio_preference="sub", preferred_resolution="1080")
        opt_sub = scraper_sub._select_preferred_source(sample_options, "Test Series", 1)
        self.assertIsNotNone(opt_sub)
        self.assertEqual(opt_sub["href"], "http://example.com/1080p-sub")

        # 2. DUB preference
        scraper_dub = AnimepaheScraper(state_manager=sm, audio_preference="dub", preferred_resolution="1080")
        opt_dub = scraper_dub._select_preferred_source(sample_options, "Test Series", 1)
        self.assertIsNotNone(opt_dub)
        self.assertEqual(opt_dub["href"], "http://example.com/1080p-eng")

        # 3. STRICT SUB preference
        dub_only_options = [{"text": "1080p (English)", "href": "http://example.com/1080p-eng"}]
        scraper_strict_sub = AnimepaheScraper(state_manager=sm, audio_preference="sub_strict", preferred_resolution="1080")
        opt_strict = scraper_strict_sub._select_preferred_source(dub_only_options, "Test Series", 2)
        self.assertIsNone(opt_strict)

        # 4. Fallback when 1080p missing (only 720p available)
        options_720_only = [
            {"text": "720p (Subbed)", "href": "http://example.com/720p-sub"},
            {"text": "480p (Subbed)", "href": "http://example.com/480p-sub"}
        ]
        # Runs 1 & 2 skip to wait for 1080p
        opt_r1 = scraper_sub._select_preferred_source(options_720_only, "Fallback Anime", 1)
        self.assertIsNone(opt_r1)
        opt_r2 = scraper_sub._select_preferred_source(options_720_only, "Fallback Anime", 1)
        self.assertIsNone(opt_r2)
        # Run 3 reaches threshold -> falls back to 720p
        opt_r3 = scraper_sub._select_preferred_source(options_720_only, "Fallback Anime", 1)
        self.assertIsNotNone(opt_r3)
        self.assertEqual(opt_r3["href"], "http://example.com/720p-sub")


    # =========================================================================
    # 5. LocalScanner Directory Scanning
    # =========================================================================
    def test_local_scanner(self):
        anime_dir = self.test_dir / "Anime Unwatched"
        anime_dir.mkdir(parents=True, exist_ok=True)

        # Series 1: standard
        s1 = anime_dir / "Series Alpha"
        s1.mkdir()
        (s1 / "Series Alpha - 01.mp4").write_bytes(b"video1")
        (s1 / "Series Alpha - 02.mp4").write_bytes(b"video2")

        # Series 2: space delimited
        s2 = anime_dir / "Series Beta"
        s2.mkdir()
        (s2 / "Series Beta 01.mkv").write_bytes(b"video1")
        (s2 / "Series Beta 02.mkv").write_bytes(b"video2")
        (s2 / "Series Beta 03.mkv").write_bytes(b"video3")
        (s2 / "extra.txt").write_bytes(b"text file")

        # Hidden / Temp folder (must be ignored)
        s_hidden = anime_dir / ".hidden_folder"
        s_hidden.mkdir()
        (s_hidden / "ignored.mp4").write_bytes(b"ignored")

        scanner = LocalScanner(target_dir=anime_dir)
        scanned = scanner.scan_unwatched()
        
        self.assertEqual(len(scanned), 2)
        names = {f.name for f in scanned}
        self.assertEqual(names, {"Series Alpha", "Series Beta"})
        
        beta_obj = next(f for f in scanned if f.name == "Series Beta")
        self.assertEqual(beta_obj.episode_numbers, {1, 2, 3})
        self.assertEqual(len(beta_obj.video_files), 3)

    # =========================================================================
    # 6. SafetyGuard Verification
    # =========================================================================
    def test_safety_guard_violations(self):
        guard = SafetyGuard(snapshot_path=Path("nonexistent_snapshot.json"))
        
        # Test 1: Writing to an existing file should raise SafetyViolationError
        existing_file = self.test_dir / "existing_file.mp4"
        existing_file.write_bytes(b"data")
        
        with self.assertRaises(SafetyViolationError):
            guard.verify_write_safety(existing_file)

        # Test 2: Writing to a new nonexistent file should succeed
        new_file = self.test_dir / "completely_new_file.mp4"
        guard.verify_write_safety(new_file)  # Should not raise

    def test_ai_helper_is_title_match(self):
        ai = AIHelper()
        # Fast path exact and season normalization
        self.assertTrue(ai.is_title_match("Solo Leveling", "Solo Leveling"))
        self.assertTrue(ai.is_title_match("Solo Leveling", "solo leveling"))
        self.assertTrue(ai.is_title_match("Arifureta S3", "Arifureta Season 3"))
        self.assertTrue(ai.is_title_match("Classroom of the Elite 3rd Season", "Classroom of the Elite Season 3"))
        self.assertTrue(ai.is_title_match("365 Days to the Wedding: Kekkon", "365 Days to the Wedding; Kekkon"))

        # Windows FS symbol-stripping: folder name is missing forbidden chars that are in the real title
        # Colon dropped: "Mecha-Ude: Mechanical Arms" -> folder "Mecha-Ude Mechanical Arms"
        self.assertTrue(ai.is_title_match("Mecha-Ude Mechanical Arms", "Mecha-Ude: Mechanical Arms"))
        # Colon dropped: subtitle separator
        self.assertTrue(ai.is_title_match("Re Zero Starting Life in Another World", "Re:Zero - Starting Life in Another World"))
        # Asterisks dropped: "Watari-kun's ****** Is About to Collapse"
        self.assertTrue(ai.is_title_match("Watari-kun's  Is About to Collapse", "Watari-kun's ****** Is About to Collapse"))
        # Slash dropped: "Sword Art Online: Alicization - War of Underworld"
        self.assertTrue(ai.is_title_match("Sword Art Online Alicization War of Underworld", "Sword Art Online: Alicization - War of Underworld"))
        # Question mark dropped: "Is It Wrong to Try to Pick Up Girls in a Dungeon?"
        self.assertTrue(ai.is_title_match("Is It Wrong to Try to Pick Up Girls in a Dungeon", "Is It Wrong to Try to Pick Up Girls in a Dungeon?"))

        # Distinct franchises without AI server running should return False (safe default)
        self.assertFalse(ai.is_title_match("Grandblue S3", "Granblue Fantasy: The Animation"))
        self.assertFalse(ai.is_title_match("Naruto Shippuden", "Bleach"))
        self.assertFalse(ai.is_title_match("", "Solo Leveling"))


    def test_closest_resolution_priority_routing(self):
        sm = StateManager(state_file=self.state_file)
        scraper = AnimepaheScraper(state_manager=sm)

        options = [
            {"text": "1080p (Subbed)", "href": "http://example.com/1080p"},
            {"text": "360p (Subbed)", "href": "http://example.com/360p"}
        ]

        # 1. Target 720p (missing 720p) -> After 3 retries, picks 1080p (next highest)
        # Runs 1 and 2 should return None (Wait & Retry)
        res_r1 = scraper._select_preferred_source(options, "Test Anime 720", 1, preferred_resolution="720")
        self.assertIsNone(res_r1)
        res_r2 = scraper._select_preferred_source(options, "Test Anime 720", 1, preferred_resolution="720")
        self.assertIsNone(res_r2)
        # Run 3 reaches threshold -> falls back to next highest (1080p)
        res_r3 = scraper._select_preferred_source(options, "Test Anime 720", 1, preferred_resolution="720")
        self.assertIsNotNone(res_r3)
        self.assertEqual(res_r3["href"], "http://example.com/1080p")

        # 2. Target 1080p (missing 1080p) -> After 3 retries, picks next lowest (720p)
        lower_options = [
            {"text": "720p (Subbed)", "href": "http://example.com/720p"},
            {"text": "480p (Subbed)", "href": "http://example.com/480p"}
        ]
        scraper._select_preferred_source(lower_options, "Test Anime 1080", 1, preferred_resolution="1080")
        scraper._select_preferred_source(lower_options, "Test Anime 1080", 1, preferred_resolution="1080")
        res_1080_r3 = scraper._select_preferred_source(lower_options, "Test Anime 1080", 1, preferred_resolution="1080")
        self.assertIsNotNone(res_1080_r3)
        self.assertEqual(res_1080_r3["href"], "http://example.com/720p")

        # 3. Exact match on run 1 -> immediate return
        exact_res = scraper._select_preferred_source(options, "Test Anime Exact", 2, preferred_resolution="1080")
        self.assertIsNotNone(exact_res)
        self.assertEqual(exact_res["href"], "http://example.com/1080p")

    def test_error_report_file_formatting(self):
        error_report_path = self.test_dir / "error.txt"
        
        entries = [
            "The anime folder named \"GrandBlue S3\" was searched and the first result returned was \"Granblue Fantasy\" which we consider different and skipped this anime. Search for \"GrandBlue S3\" gave \"Granblue Fantasy\" as its first result which is not the same anime. Please rename the folder to the anime's proper name based on the website to ensure it gets searched properly.",
            "The anime folder named \"Unknown Anime XYZ\" was searched and no results were found on the website. Please check the spelling or rename the folder to the anime's official name."
        ]
        
        # Write with single blank line separation (double newline)
        report_text = "\n\n".join(entries) + "\n"
        with open(error_report_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        self.assertTrue(error_report_path.exists())
        with open(error_report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("GrandBlue S3", content)
        self.assertIn("Unknown Anime XYZ", content)
        self.assertIn("\n\nThe anime folder named \"Unknown Anime XYZ\"", content)

        # Verify safety guard permits error.txt
        guard = SafetyGuard(snapshot_path=Path("nonexistent_snapshot.json"))
        guard.verify_write_safety(error_report_path)  # Should not raise

    def test_local_scanner_ignored(self):
        anime_dir = self.test_dir / "Anime Unwatched"
        anime_dir.mkdir(parents=True, exist_ok=True)

        # Folder 1: Normal folder
        s1 = anime_dir / "Solo Leveling"
        s1.mkdir()
        (s1 / "Solo Leveling - 01.mp4").write_bytes(b"vid1")
        (s1 / "Solo Leveling - 02.mp4").write_bytes(b"vid2")

        # Folder 2: Ignored folder "another one"
        s2 = anime_dir / "another one"
        s2.mkdir()
        (s2 / "another one - 01.mp4").write_bytes(b"vid1")

        # Folder 3: Folder with ignored file "others.txt" and "sample.mp4"
        s3 = anime_dir / "Bleach"
        s3.mkdir()
        (s3 / "Bleach - 01.mp4").write_bytes(b"vid1")
        (s3 / "Bleach - 02.mp4").write_bytes(b"vid2")
        (s3 / "sample.mp4").write_bytes(b"ignored_vid")
        (s3 / "others.txt").write_bytes(b"txt")

        # Standalone file in root: others.txt
        (anime_dir / "others.txt").write_bytes(b"root text")

        # Scanner with ignored: ['others.txt, "another one"', 'sample.mp4']
        ignored = ['others.txt, "another one"', 'sample.mp4']
        scanner = LocalScanner(target_dir=anime_dir, ignored=ignored)
        scanned = scanner.scan_unwatched()

        # "another one" must be completely ignored
        names = {f.name for f in scanned}
        self.assertIn("Solo Leveling", names)
        self.assertIn("Bleach", names)
        self.assertNotIn("another one", names)
        self.assertEqual(len(scanned), 2)

        # Bleach should only have 2 video files (sample.mp4 ignored)
        bleach_obj = next(f for f in scanned if f.name == "Bleach")
        self.assertEqual(len(bleach_obj.video_files), 2)
        bleach_file_names = {vf.name for vf in bleach_obj.video_files}
        self.assertNotIn("sample.mp4", bleach_file_names)
        self.assertNotIn("others.txt", bleach_file_names)

    def test_database_manager_crud_and_migration(self):
        db_file = self.test_dir / "test_refresher.db"
        db = DatabaseManager(db_file)

        # 1. Settings
        db.set_setting("test_key", "test_val")
        self.assertEqual(db.get_setting("test_key"), "test_val")
        db.set_bool_setting("folder_as_title", True)
        self.assertTrue(db.get_bool_setting("folder_as_title"))
        db.set_bool_setting("folder_as_title", False)
        self.assertFalse(db.get_bool_setting("folder_as_title"))

        # 2. Ignored items
        db.add_ignored_items(["Others", "another folder", "clip.mp4"])
        items = db.get_ignored_items()
        self.assertIn("Others", items)
        self.assertIn("another folder", items)
        self.assertIn("clip.mp4", items)

        removed = db.remove_ignored_items(["others", "nonexistent"])
        self.assertEqual(removed, ["Others"])
        self.assertNotIn("Others", db.get_ignored_items())

        db.clear_ignored_items()
        self.assertEqual(len(db.get_ignored_items()), 0)

        # 3. Series upsert & mapping cache
        folder_p = self.test_dir / "Solo Leveling"
        series_id = db.upsert_series(
            folder_path=folder_p,
            folder_name="Solo Leveling",
            site_title="Solo Leveling",
            site_session="a8f9c12345"
        )
        self.assertIsInstance(series_id, int)
        rec = db.get_series_by_folder_path(folder_p)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["site_session"], "a8f9c12345")
        self.assertEqual(rec["site_title"], "Solo Leveling")

        # 4. Downloaded episodes
        db.record_downloaded_episode(series_id, 1, "Solo Leveling 01.mp4", "1080p", "sub")
        db.record_downloaded_episode(series_id, 2, "Solo Leveling 02.mp4", "1080p", "sub")
        eps = db.get_downloaded_episodes_for_series(series_id)
        self.assertEqual(eps, {1, 2})
        self.assertTrue(db.is_episode_downloaded(series_id, 1))
        self.assertFalse(db.is_episode_downloaded(series_id, 3))

        # 5. History
        db.record_run_history(downloaded_count=2, error_count=0, notes="Test Run")
        # Check history recorded without exception

    def test_ai_helper_folder_indexed_filename(self):
        ai = AIHelper()
        # Default 2-digit padding
        name1 = ai.format_folder_indexed_filename("Solo Leveling", 1)
        self.assertEqual(name1, "Solo Leveling 01.mp4")
        name12 = ai.format_folder_indexed_filename("Solo Leveling", 12)
        self.assertEqual(name12, "Solo Leveling 12.mp4")

        # 3-digit padding when existing files have 3 digits
        existing_3 = ["One Piece 001.mp4", "One Piece 002.mp4"]
        name_3 = ai.format_folder_indexed_filename("One Piece", 5, existing_filenames=existing_3)
        self.assertEqual(name_3, "One Piece 005.mp4")

    def test_ai_helper_decompose_queries_and_candidate_ranking(self):
        ai = AIHelper()
        
        # Test DanMachi IV query decomposition
        queries = ai.decompose_search_queries("Is It Wrong to Try to Pick Up Girls in a Dungeon IV")
        self.assertIn("Is It Wrong to Try to Pick Up Girls in a Dungeon IV", queries)
        self.assertIn("Is It Wrong to Try to Pick Up Girls in a Dungeon", queries)

        # Test candidate ranking with multiple search results
        # User folder: "Trapped in a Dating Sim The World of Otome Games is Tough for Mobs 2"
        # Candidate 1: "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs" (Season 1)
        # Candidate 2: "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs 2nd Season" (Season 2)
        # Candidate 3: "Dating Sim Something Else"
        candidates = [
            {"title": "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs", "session": "s1_session"},
            {"title": "Trapped in a Dating Sim: The World of Otome Games is Tough for Mobs 2nd Season", "session": "s2_session"},
            {"title": "Dating Sim Something Else", "session": "s3_session"}
        ]
        best_cand, best_score, _, _ = ai.rank_and_score_candidates(
            folder_title="Trapped in a Dating Sim The World of Otome Games is Tough for Mobs 2",
            candidates=candidates,
            threshold=0.75
        )
        self.assertIsNotNone(best_cand)
        self.assertEqual(best_cand["session"], "s2_session")
        self.assertGreaterEqual(best_score, 0.85)

    def test_error_reporter_html_generation(self):
        reporter = ErrorReporter()
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

        html_path = self.test_dir / "errors.html"
        success = reporter.write_html_report(html_path)
        self.assertTrue(success)
        self.assertTrue(html_path.exists())

        html_content = html_path.read_text(encoding="utf-8")
        self.assertIn("DanMachi IV", html_content)
        self.assertIn("Dungeon ni Deai IV", html_content)
        self.assertIn("Broken Anime", html_content)
        self.assertIn("ERRORS_DATA", html_content)

    def test_downloader_touch_folder_metadata(self):
        downloader = ResilientDownloader(temp_dir=self.temp_download_dir)
        anime_dir = self.test_dir / "Anime Folder To Touch"
        anime_dir.mkdir(parents=True, exist_ok=True)

        # Set old timestamp
        old_time = time.time() - 10000
        import os
        os.utime(str(anime_dir), (old_time, old_time))
        self.assertLess(anime_dir.stat().st_mtime, time.time() - 5000)

        # Touch metadata
        success = downloader.touch_folder_metadata(anime_dir)
        self.assertTrue(success)
        # Should now be current time
        self.assertAlmostEqual(anime_dir.stat().st_mtime, time.time(), delta=5.0)

    def test_scanner_and_folder_limiting(self):
        # Create 10 dummy anime folders
        base_dir = self.test_dir / "Anime Unwatched Test"
        base_dir.mkdir(parents=True, exist_ok=True)
        for i in range(1, 11):
            f = base_dir / f"Anime Series {i:02d}"
            f.mkdir(parents=True, exist_ok=True)
            (f / f"Anime Series {i:02d} 01.mp4").write_text("dummy", encoding="utf-8")

        scanner = LocalScanner(target_dir=base_dir)
        all_folders = scanner.scan_unwatched()
        self.assertEqual(len(all_folders), 10)

        # Apply limit to 5 folders
        limited_5 = all_folders[:5]
        self.assertEqual(len(limited_5), 5)
        self.assertEqual(limited_5[0].name, "Anime Series 01")
        self.assertEqual(limited_5[4].name, "Anime Series 05")

    def test_scraper_mirror_rotation(self):
        import asyncio
        from unittest.mock import AsyncMock

        sm = StateManager(state_file=self.state_file)
        mirrors = ["https://animepahe.pw", "https://animepahe.org", "https://animepahe.com", "https://animepahe.ru"]
        scraper = AnimepaheScraper(state_manager=sm, base_urls=mirrors)
        self.assertEqual(scraper.active_base_url, "https://animepahe.pw")

        # Mock async browser methods to avoid starting real browser
        scraper._reset_browser_context = AsyncMock()
        scraper._safe_goto = AsyncMock(return_value=(None, None))
        scraper._handle_cloudflare_if_present = AsyncMock(return_value=True)

        async def run_rotation_test():
            m1 = await scraper.rotate_mirror()
            self.assertEqual(m1, "https://animepahe.org")
            m2 = await scraper.rotate_mirror()
            self.assertEqual(m2, "https://animepahe.com")
            m3 = await scraper.rotate_mirror()
            self.assertEqual(m3, "https://animepahe.ru")
            m4 = await scraper.rotate_mirror()
            self.assertEqual(m4, "https://animepahe.pw")

        asyncio.run(run_rotation_test())


if __name__ == "__main__":
    unittest.main()


