"""Centralized constants for Anime Refresher."""

from typing import Dict, List, Set, Tuple

# AI Model Configuration
# Update these values to configure or upgrade the AI model:
DEFAULT_MODEL_REPO: str = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
DEFAULT_MODEL_FILENAME: str = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
DEFAULT_MODEL_URL: str = (
    "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
)
MODEL_MIN_SIZE_BYTES: int = 300 * 1024 * 1024  # 300 MB minimum verification threshold

# System and Pipeline Defaults
DEFAULT_TARGET_FOLDER_NAME: str = "Anime Unwatched"
DEFAULT_AUDIO_PREFERENCE: str = "sub"  # Options: "sub", "dub", "sub_strict", "dub_strict"
VALID_AUDIO_PREFERENCES: Tuple[str, ...] = ("sub", "dub", "sub_strict", "dub_strict")

DEFAULT_PREFERRED_RESOLUTION: str = "1080"
VALID_RESOLUTIONS: Tuple[str, ...] = ("1080", "720", "480", "360")
RESOLUTION_PRIORITY_MAP: Dict[str, List[str]] = {
    "1080": ["1080p", "720p", "480p", "360p"],
    "720": ["720p", "1080p", "480p", "360p"],
    "480": ["480p", "720p", "1080p", "360p"],
    "360": ["360p", "480p", "720p", "1080p"],
}

DEFAULT_FOLDER_AS_TITLE: bool = True

DATABASE_FILENAME: str = "anime_refresher.db"
ERRORS_HTML_FILENAME: str = "errors.html"
ERROR_REPORT_FILENAME: str = "errors.html"

DEFAULT_SCHEDULE_TIMES: List[str] = ["06:00", "12:00", "22:00"]
DEFAULT_MIRRORS: List[str] = [
    "https://animepahe.pw",
    "https://animepahe.org",
    "https://animepahe.com",
    "https://animepahe.ru",
]

VIDEO_EXTENSIONS: Set[str] = {".mkv", ".mp4", ".ts", ".avi", ".mov", ".m4v"}
FALLBACK_MAX_RETRIES: int = 3
REQUEST_DELAY_SECONDS: int = 60

DEFAULT_STALL_TIMEOUT_SECONDS: int = 45
MIN_STALL_TIMEOUT_SECONDS: int = 30
MAX_STALL_TIMEOUT_SECONDS: int = 60

