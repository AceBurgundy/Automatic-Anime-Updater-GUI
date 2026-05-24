import os
import sys
import tempfile
import logging
from pathlib import Path
from dotenv import load_dotenv

from constants import (
    DEFAULT_MODEL_REPO,
    DEFAULT_MODEL_FILENAME,
    DEFAULT_MODEL_URL,
    MODEL_MIN_SIZE_BYTES,
    POSTER_FILENAME,
    POSTER_CSS_SELECTOR,
    DEFAULT_TARGET_FOLDER_NAME,
    DEFAULT_AUDIO_PREFERENCE,
    VALID_AUDIO_PREFERENCES,
    DEFAULT_PREFERRED_RESOLUTION,
    VALID_RESOLUTIONS,
    RESOLUTION_PRIORITY_MAP,
    DEFAULT_FOLDER_AS_TITLE,
    DATABASE_FILENAME,
    ERRORS_HTML_FILENAME,
    ERROR_REPORT_FILENAME,
    DEFAULT_SCHEDULE_TIMES,
    DEFAULT_MIRRORS,
    VIDEO_EXTENSIONS,
    FALLBACK_MAX_RETRIES as CONST_FALLBACK_RETRIES,
    REQUEST_DELAY_SECONDS as CONST_REQUEST_DELAY,
)
from core.database import DatabaseManager

# Base project directory
PROJECT_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(PROJECT_DIR / ".env")

# Database instance & auto-migration
DATABASE_PATH = PROJECT_DIR / DATABASE_FILENAME
db_manager = DatabaseManager(DATABASE_PATH)

# Models directory
MODELS_DIR = PROJECT_DIR / "models"
MODEL_URL = os.getenv("MODEL_URL", DEFAULT_MODEL_URL)
MODEL_FILENAME = os.getenv("MODEL_FILENAME", DEFAULT_MODEL_FILENAME)
MODEL_PATH = MODELS_DIR / MODEL_FILENAME

# Target anime unwatched directory
_raw_target = os.getenv("TARGET_DIR", "").strip()
if _raw_target:
    TARGET_DIR = Path(_raw_target)
else:
    TARGET_DIR = Path(r"D:\Videos") / DEFAULT_TARGET_FOLDER_NAME

# Audio preference: "sub", "dub", "sub_strict", "dub_strict"
_raw_audio = os.getenv("AUDIO_PREFERENCE", DEFAULT_AUDIO_PREFERENCE).strip().lower()
AUDIO_PREFERENCE = _raw_audio if _raw_audio in VALID_AUDIO_PREFERENCES else DEFAULT_AUDIO_PREFERENCE

# Preferred resolution: "1080", "720", "480", "360"
_raw_res = os.getenv("PREFERRED_RESOLUTION", DEFAULT_PREFERRED_RESOLUTION).strip().lower().rstrip("p")
PREFERRED_RESOLUTION = _raw_res if _raw_res in VALID_RESOLUTIONS else DEFAULT_PREFERRED_RESOLUTION

# Error report file path
ERRORS_HTML_PATH = TARGET_DIR / ERRORS_HTML_FILENAME
ERROR_REPORT_PATH = ERRORS_HTML_PATH

# Poster configuration
DOWNLOAD_POSTERS = os.getenv("DOWNLOAD_POSTERS", "true").lower() in ("true", "1", "yes")

# Temp directory defaults to Windows %TEMP%\anime-refresher
_custom_temp = os.getenv("TEMP_DIR", "").strip()
if _custom_temp:
    TEMP_DIR = Path(_custom_temp)
else:
    TEMP_DIR = Path(tempfile.gettempdir()) / "anime-refresher"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Animepahe mirror URLs (failover list)
_raw_urls = os.getenv("BASE_URLS", ",".join(DEFAULT_MIRRORS))
BASE_URLS = [url.strip().rstrip("/") for url in _raw_urls.split(",") if url.strip()]

# Ollama configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma_2B_basic")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Schedule times
_raw_sched = os.getenv("SCHEDULE_TIMES", ",".join(DEFAULT_SCHEDULE_TIMES))
SCHEDULE_TIMES = [t.strip() for t in _raw_sched.split(",") if t.strip()]

# Fallback & Retry settings
FALLBACK_MAX_RETRIES = int(os.getenv("FALLBACK_MAX_RETRIES", str(CONST_FALLBACK_RETRIES)))
REQUEST_DELAY_SECONDS = int(os.getenv("REQUEST_DELAY_SECONDS", str(CONST_REQUEST_DELAY)))
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "camoufox").lower()

# Legacy files (for auto-migration) & Log files
STATE_FILE = PROJECT_DIR / "state.json"
IGNORED_FILE = PROJECT_DIR / "ignored.json"
LOG_FILE = PROJECT_DIR / "anime_refresher.log"

# Migrate legacy state.json and ignored.json if they exist
db_manager.migrate_legacy_files_if_needed(state_file=STATE_FILE, ignored_file=IGNORED_FILE)


def setup_logging(verbose: bool = False, stream_events: bool = False) -> logging.Logger:
    """Configures rotating/standard file logger and console logger."""
    logger = logging.getLogger("anime_refresher")
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # File handler (silent, complete logs)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console stream handler
    # When stream_events is active, send regular logs to stderr so stdout is pure JSON
    out_stream = sys.stderr if stream_events else sys.stdout
    console_handler = logging.StreamHandler(out_stream)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger
