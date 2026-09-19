from dataclasses import dataclass
from logging import Logger, getLogger
from pathlib import Path
from typing import Dict, List, Optional, Set

from config import TARGET_DIR, VIDEO_EXTENSIONS
from core.ai_helper import AIHelper

logger: Logger = getLogger("anime_refresher.scanner")


@dataclass
class AnimeLocalState:
    """
    Data container representing the on-disk state of an individual anime folder.

    Attributes
    ----------
    folder_name : str
        Directory basename of the series.
    folder_path : Path
        Absolute path to the anime directory.
    existing_files : List[str]
        List of all existing media file basenames.
    downloaded_episodes : Set[int]
        Set of episode integers detected locally.
    """

    folder_name: str
    folder_path: Path
    existing_files: List[str]
    downloaded_episodes: Set[int]


@dataclass
class AnimeFolder:
    """
    Represents a scanned local anime folder with parsed video file inventory.

    Attributes
    ----------
    name : str
        Directory basename of the series.
    path : Path
        Absolute path to the series folder.
    video_files : List[Path]
        List of absolute paths to video files contained within the folder.
    episode_numbers : Set[int]
        Set of parsed episode sequence numbers found locally.
    """

    name: str
    path: Path
    video_files: List[Path]
    episode_numbers: Set[int]


class LocalScanner:
    """
    Filesystem scanner that catalogs anime series directories and parses local episodes.

    Attributes
    ----------
    target_dir : Path
        Base directory containing local anime series folders.
    ai_helper : AIHelper
        Helper instance used for title cleaning and episode number extraction.
    ignored : List[str]
        Raw list of excluded folder or file pattern strings.
    _normalized_ignored : Set[str]
        Set of normalized, lowercase exclusion patterns for fast matching.
    """

    target_dir: Path
    ai_helper: AIHelper
    ignored: List[str]
    _normalized_ignored: Set[str]

    def __init__(
        self,
        target_dir: Path = TARGET_DIR,
        ai_helper: Optional[AIHelper] = None,
        ignored: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the local filesystem scanner for unwatched anime directories.

        Parameters
        ----------
        target_dir : Path, default=TARGET_DIR
            Base directory containing local anime series folders.
        ai_helper : Optional[AIHelper], default=None
            Instance of AIHelper used for parsing episode numbers.
        ignored : Optional[List[str]], default=None
            List of folder or file names / paths to exclude from scanning.
        """
        self.target_dir: Path = target_dir
        self.ai_helper: AIHelper = ai_helper if ai_helper is not None else AIHelper()
        self.ignored: List[str] = ignored if ignored is not None else []
        self._normalized_ignored: Set[str] = self._normalize_ignored(self.ignored)

    def _normalize_ignored(self, ignored: List[str]) -> Set[str]:
        """
        Normalize ignored strings, handling comma-separated tokens, quotes, and path separators.

        Parameters
        ----------
        ignored : List[str]
            Raw list of ignored tokens, paths, or names.

        Returns
        -------
        Set[str]
            Normalized set of lowercase strings and path representations.
        """
        normalized_ignored: Set[str] = set()
        for item in ignored:
            if not item:
                continue
            for part in str(item).split(","):
                cleaned_part: str = part.strip().strip("'\"").strip()
                if cleaned_part:
                    normalized_ignored.add(cleaned_part.lower())
                    normalized_ignored.add(Path(cleaned_part).name.lower())
                    normalized_ignored.add(cleaned_part.replace("\\", "/").lower().strip("/"))
        return normalized_ignored

    def is_ignored(self, path: Path) -> bool:
        """
        Determine whether a file or directory path is in the ignored set.

        Parameters
        ----------
        path : Path
            File or directory path to check against the ignored collection.

        Returns
        -------
        bool
            True if the path matches an ignored rule, False otherwise.
        """
        if not self._normalized_ignored:
            return False

        # 1. Direct name match (e.g. 'Others' or 'another one')
        name_lower: str = path.name.lower()
        if name_lower in self._normalized_ignored:
            return True

        # 2. Relative path from target_dir (e.g. 'another one' or 'Series/others.txt')
        try:
            relative_path: str = path.relative_to(self.target_dir).as_posix().lower()
            if relative_path in self._normalized_ignored:
                return True
        except ValueError:
            pass

        # 3. Direct path string check
        path_string: str = str(path).replace("\\", "/").lower()
        for item in self._normalized_ignored:
            if path_string.endswith(f"/{item}") or path_string == item:
                return True

        return False

    def scan_unwatched(self) -> List[AnimeFolder]:
        """
        Scan the target directory and return list of AnimeFolder instances, respecting ignored items.

        Returns
        -------
        List[AnimeFolder]
            List of detected anime series directories and their contents.
        """
        if not self.target_dir.exists():
            logger.error(f"Target directory {self.target_dir} does not exist!")
            return []

        folders: List[AnimeFolder] = []
        for entry in self.target_dir.iterdir():
            if not entry.is_dir():
                continue

            if entry.name.startswith(".") or entry.name.lower() in ("temp", "$recycle.bin"):
                continue

            if self.is_ignored(entry):
                logger.info(f"Skipping ignored folder: '{entry.name}'")
                continue

            video_files: List[Path] = [
                file_path
                for file_path in entry.iterdir()
                if file_path.is_file()
                and file_path.suffix.lower() in VIDEO_EXTENSIONS
                and not self.is_ignored(file_path)
            ]
            file_names: List[str] = [file_path.name for file_path in video_files]
            episode_numbers: Set[int] = self.ai_helper.parse_episode_numbers(file_names)

            folders.append(
                AnimeFolder(
                    name=entry.name,
                    path=entry,
                    video_files=video_files,
                    episode_numbers=episode_numbers,
                )
            )

        logger.info(f"Scanned {len(folders)} local anime directories in {self.target_dir}")
        return folders

    def scan(self) -> Dict[str, AnimeLocalState]:
        """
        Scan the unwatched anime target directory and return mapping of folder name to state.

        Returns
        -------
        Dict[str, AnimeLocalState]
            Dictionary mapping folder name to AnimeLocalState.
        """
        unwatched_folders: List[AnimeFolder] = self.scan_unwatched()
        results: Dict[str, AnimeLocalState] = {}
        for folder in unwatched_folders:
            results[folder.name] = AnimeLocalState(
                folder_name=folder.name,
                folder_path=folder.path,
                existing_files=[video_file.name for video_file in folder.video_files],
                downloaded_episodes=folder.episode_numbers,
            )
        return results
