"""Centralized constants for Anime Refresher."""

from pathlib import Path

# AI MODEL CONFIGURATION
# To change or upgrade the AI model in the future, update these values:
DEFAULT_MODEL_REPO = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
DEFAULT_MODEL_FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
DEFAULT_MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
)
MODEL_MIN_SIZE_BYTES = 300 * 1024 * 1024  # 300 MB minimum verification threshold

# SYSTEM & PIPELINE DEFAULTS

DEFAULT_TARGET_FOLDER_NAME = "Anime Unwatched"
DEFAULT_AUDIO_PREFERENCE = "sub"  # Options: "sub", "dub", "sub_strict", "dub_strict"
VALID_AUDIO_PREFERENCES = ("sub", "dub", "sub_strict", "dub_strict")

DEFAULT_PREFERRED_RESOLUTION = "1080"
VALID_RESOLUTIONS = ("1080", "720", "480", "360")
RESOLUTION_PRIORITY_MAP = {
    "1080": ["1080p", "720p", "480p", "360p"],
    "720": ["720p", "1080p", "480p", "360p"],
    "480": ["480p", "720p", "1080p", "360p"],
    "360": ["360p", "480p", "720p", "1080p"],
}

DEFAULT_FOLDER_AS_TITLE = True

DATABASE_FILENAME = "anime_refresher.db"
ERRORS_HTML_FILENAME = "errors.html"
ERROR_REPORT_FILENAME = "errors.html"

DEFAULT_SCHEDULE_TIMES = ["06:00", "12:00", "22:00"]
DEFAULT_MIRRORS = [
    "https://animepahe.pw",
    "https://animepahe.org",
    "https://animepahe.com",
    "https://animepahe.ru",
]

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".ts", ".avi", ".mov", ".m4v"}
FALLBACK_MAX_RETRIES = 3
REQUEST_DELAY_SECONDS = 60

