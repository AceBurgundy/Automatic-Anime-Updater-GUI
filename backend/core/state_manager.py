import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from config import STATE_FILE

logger = logging.getLogger("anime_refresher.state")

class StateManager:
    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read state file {self.state_file}: {e}. Creating new state.")
        return {
            "fallback_retries": {},
            "history": []
        }

    def save(self) -> None:
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write state file {self.state_file}: {e}")

    def get_viewed_count(self, anime_title: str, episode_num: int) -> int:
        retries = self.data.get("fallback_retries", {})
        anime_retries = retries.get(anime_title, {})
        return anime_retries.get(str(episode_num), 0)

    def increment_viewed_count(self, anime_title: str, episode_num: int) -> int:
        if "fallback_retries" not in self.data:
            self.data["fallback_retries"] = {}
        if anime_title not in self.data["fallback_retries"]:
            self.data["fallback_retries"][anime_title] = {}
        
        current = self.data["fallback_retries"][anime_title].get(str(episode_num), 0)
        new_count = current + 1
        self.data["fallback_retries"][anime_title][str(episode_num)] = new_count
        self.save()
        return new_count

    def reset_viewed_count(self, anime_title: str, episode_num: int) -> None:
        if "fallback_retries" in self.data and anime_title in self.data["fallback_retries"]:
            if str(episode_num) in self.data["fallback_retries"][anime_title]:
                del self.data["fallback_retries"][anime_title][str(episode_num)]
                self.save()

    def record_downloaded_episode(self, anime_title: str, episode_num: int, filename: str) -> None:
        """Records a completed episode download in the state history."""
        if "downloaded_episodes" not in self.data:
            self.data["downloaded_episodes"] = {}
        if anime_title not in self.data["downloaded_episodes"]:
            self.data["downloaded_episodes"][anime_title] = []

        entry = {
            "episode": episode_num,
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        }
        # Avoid duplicate entries
        if not any(e.get("episode") == episode_num for e in self.data["downloaded_episodes"][anime_title]):
            self.data["downloaded_episodes"][anime_title].append(entry)
            self.save()
            logger.debug(f"Recorded downloaded episode for '{anime_title}': Ep {episode_num} ({filename})")

    def is_episode_downloaded(self, anime_title: str, episode_num: int) -> bool:
        """Checks if an episode has been recorded as downloaded in state."""
        downloads = self.data.get("downloaded_episodes", {}).get(anime_title, [])
        return any(e.get("episode") == episode_num for e in downloads)

    def get_downloaded_episodes(self, anime_title: str) -> List[int]:
        """Returns a list of all downloaded episode numbers recorded in state for a series."""
        downloads = self.data.get("downloaded_episodes", {}).get(anime_title, [])
        return [e["episode"] for e in downloads if "episode" in e]

    def record_run(self, downloaded: int, errors: int, notes: str = "") -> None:
        if "history" not in self.data:
            self.data["history"] = []
        
        self.data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "downloaded": downloaded,
            "errors": errors,
            "notes": notes
        })
        # Keep only the last 50 runs in history
        self.data["history"] = self.data["history"][-50:]
        self.save()

