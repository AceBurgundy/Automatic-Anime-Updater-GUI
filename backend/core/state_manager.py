from datetime import datetime
from json import dump as json_dump, load as json_load
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Dict, List

from config import STATE_FILE

logger: Logger = getLogger("anime_refresher.state")


class StateManager:
    """
    Persistent state manager storing anime retry attempts and run history.

    Attributes
    ----------
    state_file : Path
        File system path to the state JSON persistence file.
    data : Dict[str, Any]
        In-memory dictionary cache of state information.
    """

    state_file: Path
    data: Dict[str, Any]

    def __init__(self, state_file: Path = STATE_FILE) -> None:
        """
        Initialize the persistent JSON state manager.

        Parameters
        ----------
        state_file : Path, default=STATE_FILE
            Path to the JSON state storage file.
        """
        self.state_file: Path = state_file
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """
        Load state data from disk, creating default schema if missing or corrupted.

        Returns
        -------
        Dict[str, Any]
            State dictionary containing retry records and execution history.
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as file_handle:
                    return json_load(file_handle)
            except Exception as read_error:
                logger.warning(
                    f"Failed to read state file {self.state_file}: {read_error}. Creating new state."
                )
        return {
            "fallback_retries": {},
            "history": [],
        }

    def save(self) -> None:
        """
        Persist current in-memory state dictionary to disk.
        """
        try:
            with open(self.state_file, "w", encoding="utf-8") as file_handle:
                json_dump(self.data, file_handle, indent=2)
        except Exception as write_error:
            logger.error(f"Failed to write state file {self.state_file}: {write_error}")

    def get_viewed_count(self, anime_title: str, episode_num: int) -> int:
        """
        Get the number of fallback attempts recorded for a specific episode.

        Parameters
        ----------
        anime_title : str
            Title of the anime series.
        episode_num : int
            Episode sequence number.

        Returns
        -------
        int
            Recorded retry attempt count.
        """
        retries: Dict[str, Any] = self.data.get("fallback_retries", {})
        anime_retries: Dict[str, int] = retries.get(anime_title, {})
        return anime_retries.get(str(episode_num), 0)

    def increment_viewed_count(self, anime_title: str, episode_num: int) -> int:
        """
        Increment and persist the retry count for an episode.

        Parameters
        ----------
        anime_title : str
            Title of the anime series.
        episode_num : int
            Episode sequence number.

        Returns
        -------
        int
            Updated retry attempt count.
        """
        if "fallback_retries" not in self.data:
            self.data["fallback_retries"] = {}
        if anime_title not in self.data["fallback_retries"]:
            self.data["fallback_retries"][anime_title] = {}

        current_count: int = self.data["fallback_retries"][anime_title].get(str(episode_num), 0)
        new_count: int = current_count + 1
        self.data["fallback_retries"][anime_title][str(episode_num)] = new_count
        self.save()
        return new_count

    def reset_viewed_count(self, anime_title: str, episode_num: int) -> None:
        """
        Clear fallback retry count for an episode upon successful download.

        Parameters
        ----------
        anime_title : str
            Title of the anime series.
        episode_num : int
            Episode sequence number.
        """
        if "fallback_retries" in self.data and anime_title in self.data["fallback_retries"]:
            if str(episode_num) in self.data["fallback_retries"][anime_title]:
                del self.data["fallback_retries"][anime_title][str(episode_num)]
                self.save()

    def record_downloaded_episode(self, anime_title: str, episode_num: int, filename: str) -> None:
        """
        Record a completed episode download in the state history.

        Parameters
        ----------
        anime_title : str
            Title of the anime series.
        episode_num : int
            Episode sequence number.
        filename : str
            Filename of the downloaded video.
        """
        if "downloaded_episodes" not in self.data:
            self.data["downloaded_episodes"] = {}
        if anime_title not in self.data["downloaded_episodes"]:
            self.data["downloaded_episodes"][anime_title] = []

        entry: Dict[str, Any] = {
            "episode": episode_num,
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
        }
        # Avoid duplicate entries
        if not any(
            existing.get("episode") == episode_num
            for existing in self.data["downloaded_episodes"][anime_title]
        ):
            self.data["downloaded_episodes"][anime_title].append(entry)
            self.save()
            logger.debug(
                f"Recorded downloaded episode for '{anime_title}': Ep {episode_num} ({filename})"
            )

    def is_episode_downloaded(self, anime_title: str, episode_num: int) -> bool:
        """
        Check if an episode has been recorded as downloaded in state.

        Parameters
        ----------
        anime_title : str
            Title of the anime series.
        episode_num : int
            Episode sequence number.

        Returns
        -------
        bool
            True if recorded as downloaded, False otherwise.
        """
        downloads: List[Dict[str, Any]] = self.data.get("downloaded_episodes", {}).get(
            anime_title, []
        )
        return any(entry.get("episode") == episode_num for entry in downloads)

    def get_downloaded_episodes(self, anime_title: str) -> List[int]:
        """
        Return a list of all downloaded episode numbers recorded in state for a series.

        Parameters
        ----------
        anime_title : str
            Title of the anime series.

        Returns
        -------
        List[int]
            List of downloaded episode sequence numbers.
        """
        downloads: List[Dict[str, Any]] = self.data.get("downloaded_episodes", {}).get(
            anime_title, []
        )
        return [entry["episode"] for entry in downloads if "episode" in entry]

    def record_run(self, downloaded: int, errors: int, notes: str = "") -> None:
        """
        Append a cycle execution entry to the history ledger (capped at 50 runs).

        Parameters
        ----------
        downloaded : int
            Count of newly downloaded episodes in the cycle.
        errors : int
            Count of errors encountered in the cycle.
        notes : str, default=""
            Optional contextual run notes.
        """
        if "history" not in self.data:
            self.data["history"] = []

        self.data["history"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "downloaded": downloaded,
                "errors": errors,
                "notes": notes,
            }
        )
        # Keep only the last 50 runs in history
        self.data["history"] = self.data["history"][-50:]
        self.save()
