import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set
from config import TARGET_DIR, VIDEO_EXTENSIONS
from core.ai_helper import AIHelper

logger = logging.getLogger("anime_refresher.scanner")

@dataclass
class AnimeLocalState:
    folder_name: str
    folder_path: Path
    existing_files: List[str]
    downloaded_episodes: Set[int]

@dataclass
class AnimeFolder:
    name: str
    path: Path
    video_files: List[Path]
    episode_numbers: Set[int]

class LocalScanner:
    def __init__(
        self,
        target_dir: Path = TARGET_DIR,
        ai_helper: AIHelper = None,
        ignored: Optional[List[str]] = None
    ):
        self.target_dir = target_dir
        self.ai_helper = ai_helper or AIHelper()
        self.ignored = ignored or []
        self._normalized_ignored = self._normalize_ignored(self.ignored)

    def _normalize_ignored(self, ignored: List[str]) -> Set[str]:
        """Normalizes ignored strings, handling comma-separated tokens, quotes, and path separators."""
        norm = set()
        for item in ignored:
            if not item:
                continue
            for part in str(item).split(","):
                clean = part.strip().strip("'\"").strip()
                if clean:
                    norm.add(clean.lower())
                    norm.add(Path(clean).name.lower())
                    norm.add(clean.replace("\\", "/").lower().strip("/"))
        return norm

    def is_ignored(self, path: Path) -> bool:
        """Determines whether a file or directory path is in the ignored list."""
        if not self._normalized_ignored:
            return False

        # 1. Direct name match (e.g. 'Others' or 'another one')
        name_lower = path.name.lower()
        if name_lower in self._normalized_ignored:
            return True

        # 2. Relative path from target_dir (e.g. 'another one' or 'Series/others.txt')
        try:
            rel_path = path.relative_to(self.target_dir).as_posix().lower()
            if rel_path in self._normalized_ignored:
                return True
        except ValueError:
            pass

        # 3. Direct path string check
        path_str = str(path).replace("\\", "/").lower()
        for item in self._normalized_ignored:
            if path_str.endswith(f"/{item}") or path_str == item:
                return True

        return False

    def scan_unwatched(self) -> List[AnimeFolder]:
        """Scans the target directory and returns list of AnimeFolder instances, respecting ignored items."""
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

            video_files = [
                f for f in entry.iterdir()
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS and not self.is_ignored(f)
            ]
            file_names = [f.name for f in video_files]
            episodes = self.ai_helper.parse_episode_numbers(file_names)

            folders.append(AnimeFolder(
                name=entry.name,
                path=entry,
                video_files=video_files,
                episode_numbers=episodes
            ))

        logger.info(f"Scanned {len(folders)} local anime directories in {self.target_dir}")
        return folders

    def scan(self) -> Dict[str, AnimeLocalState]:
        """Scans the unwatched anime target directory and returns mapping of folder name to state."""
        unwatched = self.scan_unwatched()
        results: Dict[str, AnimeLocalState] = {}
        for f in unwatched:
            results[f.name] = AnimeLocalState(
                folder_name=f.name,
                folder_path=f.path,
                existing_files=[vf.name for vf in f.video_files],
                downloaded_episodes=f.episode_numbers
            )
        return results
