import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger("anime_refresher.safety")

SNAPSHOT_JSON = Path(r"D:\Conversations\anime-refresher\anime_unwatched_snapshot.json")

class SafetyViolationError(Exception):
    """Raised when an operation attempts to write, edit, rename, or delete a snapshot file."""
    pass

class SafetyGuard:
    _instance = None
    _protected_files: Set[str] = set()

    def __init__(self, snapshot_path: Path = SNAPSHOT_JSON):
        self.snapshot_path = snapshot_path
        self._load_snapshot()

    def _load_snapshot(self):
        if not self.snapshot_path.exists():
            logger.warning(f"Safety snapshot {self.snapshot_path} not found. Operating with disk existence checks.")
            return

        try:
            with open(self.snapshot_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for rel_root, content in data.items():
                for filename in content.get("files", []):
                    rel_path = (Path(rel_root) / filename).as_posix().lower() if rel_root != "." else Path(filename).as_posix().lower()
                    self._protected_files.add(rel_path)
                    # Also record raw filename
                    self._protected_files.add(filename.lower())

            logger.info(f"[SafetyGuard] Loaded {len(self._protected_files)} protected entries from snapshot. Write protection active.")
        except Exception as e:
            logger.error(f"[SafetyGuard] Error loading safety snapshot: {e}")

    def verify_write_safety(self, target_file_path: Path):
        """
        Guarantees that target_file_path does not touch any snapshot-protected file.
        Throws SafetyViolationError if target is in the protected list or already exists.
        """
        filename = target_file_path.name.lower()
        if filename in ("errors.html", "error.txt", "anime_refresher.db", "anime_refresher.db-wal", "anime_refresher.db-shm"):
            # Runtime report and database files are permitted
            return

        if filename in self._protected_files:
            raise SafetyViolationError(
                f"[SAFETY VIOLATION] Refusing write access to protected snapshot file: '{target_file_path.name}'"
            )

        if target_file_path.exists():
            raise SafetyViolationError(
                f"[SAFETY VIOLATION] Target file already exists on disk: '{target_file_path}'"
            )

        logger.debug(f"[SafetyGuard] File '{target_file_path.name}' passed safety check (new file).")

safety_guard = SafetyGuard()

