from logging import (
    DEBUG,
    INFO,
    FileHandler,
    Formatter,
    Logger,
    StreamHandler,
    getLogger,
)
from os import getenv
from pathlib import Path
from sys import stderr, stdout
from tempfile import gettempdir
from typing import List, TextIO

from dotenv import load_dotenv

from constants import (
    DEFAULT_MODEL_REPO,
    DEFAULT_MODEL_FILENAME,
    DEFAULT_MODEL_URL,
    MODEL_MIN_SIZE_BYTES,
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
    DEFAULT_STALL_TIMEOUT_SECONDS,
    MIN_STALL_TIMEOUT_SECONDS,
    MAX_STALL_TIMEOUT_SECONDS,
)
from core.database import DatabaseManager

# Base project directory
PROJECT_DIR: Path = Path(__file__).resolve().parent

# Load .env file
load_dotenv(PROJECT_DIR / ".env")

# Database instance & auto-migration
DATABASE_PATH: Path = PROJECT_DIR / DATABASE_FILENAME
db_manager: DatabaseManager = DatabaseManager(DATABASE_PATH)

# Models directory
MODELS_DIR: Path = PROJECT_DIR / "models"
MODEL_URL: str = getenv("MODEL_URL", DEFAULT_MODEL_URL)
MODEL_FILENAME: str = getenv("MODEL_FILENAME", DEFAULT_MODEL_FILENAME)
MODEL_PATH: Path = MODELS_DIR / MODEL_FILENAME

# Target anime unwatched directory
raw_target_directory: str = getenv("TARGET_DIR", "").strip()
if raw_target_directory:
    TARGET_DIR: Path = Path(raw_target_directory)
else:
    TARGET_DIR: Path = Path(r"D:\Videos") / DEFAULT_TARGET_FOLDER_NAME

# Audio preference: "sub", "dub", "sub_strict", "dub_strict"
raw_audio_preference: str = getenv("AUDIO_PREFERENCE", DEFAULT_AUDIO_PREFERENCE).strip().lower()
AUDIO_PREFERENCE: str = (
    raw_audio_preference
    if raw_audio_preference in VALID_AUDIO_PREFERENCES
    else DEFAULT_AUDIO_PREFERENCE
)

# Preferred resolution: "1080", "720", "480", "360"
raw_resolution_preference: str = (
    getenv("PREFERRED_RESOLUTION", DEFAULT_PREFERRED_RESOLUTION).strip().lower().rstrip("p")
)
PREFERRED_RESOLUTION: str = (
    raw_resolution_preference
    if raw_resolution_preference in VALID_RESOLUTIONS
    else DEFAULT_PREFERRED_RESOLUTION
)

# Error report file path
ERRORS_HTML_PATH: Path = TARGET_DIR / ERRORS_HTML_FILENAME
ERROR_REPORT_PATH: Path = ERRORS_HTML_PATH

# Temp directory defaults to Windows %TEMP%\anime-refresher
custom_temp_directory: str = getenv("TEMP_DIR", "").strip()
if custom_temp_directory:
    TEMP_DIR: Path = Path(custom_temp_directory)
else:
    TEMP_DIR: Path = Path(gettempdir()) / "anime-refresher"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Animepahe mirror URLs (failover list)
raw_mirror_urls: str = getenv("BASE_URLS", ",".join(DEFAULT_MIRRORS))
BASE_URLS: List[str] = [
    mirror_url.strip().rstrip("/")
    for mirror_url in raw_mirror_urls.split(",")
    if mirror_url.strip()
]

# Ollama configuration
OLLAMA_MODEL: str = getenv("OLLAMA_MODEL", "gemma_2B_basic")
OLLAMA_HOST: str = getenv("OLLAMA_HOST", "http://localhost:11434")

# Schedule times
raw_schedule_times: str = getenv("SCHEDULE_TIMES", ",".join(DEFAULT_SCHEDULE_TIMES))
SCHEDULE_TIMES: List[str] = [
    schedule_time.strip()
    for schedule_time in raw_schedule_times.split(",")
    if schedule_time.strip()
]

# Fallback & Retry settings
FALLBACK_MAX_RETRIES: int = int(getenv("FALLBACK_MAX_RETRIES", str(CONST_FALLBACK_RETRIES)))
REQUEST_DELAY_SECONDS: int = int(getenv("REQUEST_DELAY_SECONDS", str(CONST_REQUEST_DELAY)))
HEADLESS: bool = getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
BROWSER_TYPE: str = getenv("BROWSER_TYPE", "camoufox").lower()

# Inactivity / Stall Watchdog settings
raw_stall_timeout: str = getenv(
    "STALL_TIMEOUT_SECONDS", str(DEFAULT_STALL_TIMEOUT_SECONDS)
).strip()
try:
    parsed_stall_timeout: int = int(raw_stall_timeout)
    STALL_TIMEOUT_SECONDS: int = max(
        MIN_STALL_TIMEOUT_SECONDS,
        min(parsed_stall_timeout, MAX_STALL_TIMEOUT_SECONDS),
    )
except ValueError:
    STALL_TIMEOUT_SECONDS: int = DEFAULT_STALL_TIMEOUT_SECONDS


# Legacy files (for auto-migration) & Log files
STATE_FILE: Path = PROJECT_DIR / "state.json"
IGNORED_FILE: Path = PROJECT_DIR / "ignored.json"
LOG_FILE: Path = PROJECT_DIR / "anime_refresher.log"

# Migrate legacy state.json and ignored.json if they exist
db_manager.migrate_legacy_files_if_needed(state_file=STATE_FILE, ignored_file=IGNORED_FILE)


def setup_logging(verbose: bool = False, stream_events: bool = False) -> Logger:
    """
    Configure rotating/standard file logger and console logger.

    Parameters
    ----------
    verbose : bool, default=False
        Whether to enable debug logging output to the console.
    stream_events : bool, default=False
        Whether to route standard logs to stderr so stdout remains clean for events.

    Returns
    -------
    Logger
        Configured logger instance for the application.
    """
    logger: Logger = getLogger("anime_refresher")
    logger.setLevel(DEBUG)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # File handler (silent, complete logs)
    file_handler: FileHandler = FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(DEBUG)
    file_formatter: Formatter = Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console stream handler
    # When stream_events is active, send regular logs to stderr so stdout is pure JSON
    output_stream: TextIO = stderr if stream_events else stdout
    console_handler: StreamHandler = StreamHandler(output_stream)
    console_handler.setLevel(DEBUG if verbose else INFO)
    console_formatter: Formatter = Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
