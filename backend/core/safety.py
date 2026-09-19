from json import load as json_load
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger: Logger = getLogger("anime_refresher.safety")

SNAPSHOT_JSON: Path = Path(r"D:\Conversations\anime-refresher\anime_unwatched_snapshot.json")


class SafetyViolationError(Exception):
    """
    Exception raised when an operation attempts to write, edit, rename, or delete a snapshot file.
    """

    pass


class SafetyGuard:
    """
    Programmatic file system guard preventing overwriting or tampering with protected anime files.

    Attributes
    ----------
    snapshot_path : Path
        Path to the JSON snapshot file containing protected file basenames and relative paths.
    _protected_files : Set[str]
        Set of protected file paths and lowercase basenames.
    _instance : Optional[SafetyGuard]
        Singleton instance reference if applicable.
    """

    _instance: Optional["SafetyGuard"] = None
    _protected_files: Set[str] = set()
    snapshot_path: Path

    def __init__(self, snapshot_path: Path = SNAPSHOT_JSON) -> None:
        """
        Initialize write safety guard backed by initial state snapshot.

        Parameters
        ----------
        snapshot_path : Path, default=SNAPSHOT_JSON
            Path to the JSON snapshot file containing protected file basenames and relative paths.
        """
        self.snapshot_path: Path = snapshot_path
        self._protected_files: Set[str] = set()
        self._load_snapshot()

    def _load_snapshot(self) -> None:
        """
        Load protected file names and relative paths from the snapshot JSON file.
        """
        if not self.snapshot_path.exists():
            logger.warning(
                f"Safety snapshot {self.snapshot_path} not found. Operating with disk existence checks."
            )
            return

        try:
            with open(self.snapshot_path, "r", encoding="utf-8") as file_handle:
                snapshot_data: Dict[str, Any] = json_load(file_handle)

            for relative_root, content in snapshot_data.items():
                file_list: List[str] = content.get("files", [])
                for filename in file_list:
                    relative_path: str = (
                        (Path(relative_root) / filename).as_posix().lower()
                        if relative_root != "."
                        else Path(filename).as_posix().lower()
                    )
                    self._protected_files.add(relative_path)
                    # Also record raw lowercase filename
                    self._protected_files.add(filename.lower())

            logger.info(
                f"[SafetyGuard] Loaded {len(self._protected_files)} protected entries from snapshot. "
                "Write protection active."
            )
        except Exception as load_error:
            logger.error(f"[SafetyGuard] Error loading safety snapshot: {load_error}")

    def verify_write_safety(self, target_file_path: Path) -> None:
        """
        Guarantee that target_file_path does not touch any snapshot-protected file.

        Parameters
        ----------
        target_file_path : Path
            Proposed destination file path to validate.

        Raises
        ------
        SafetyViolationError
            If target_file_path matches a protected file or already exists on disk.
        """
        filename: str = target_file_path.name.lower()
        if filename in (
            "errors.html",
            "error.txt",
            "anime_refresher.db",
            "anime_refresher.db-wal",
            "anime_refresher.db-shm",
        ):
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


safety_guard: SafetyGuard = SafetyGuard()
