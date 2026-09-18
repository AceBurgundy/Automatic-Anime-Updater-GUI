from contextlib import contextmanager
from datetime import datetime, timezone
from json import loads as json_loads
from logging import Logger, getLogger
from pathlib import Path
from sqlite3 import Connection, Cursor, Error as SqliteError, Row, connect as sqlite3_connect
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

logger: Logger = getLogger("anime_refresher.database")


class DatabaseManager:
    """Thread-safe SQLite3 database manager for Anime Refresher state, cache, and settings."""

    db_path: Path

    def __init__(self, db_path: Path) -> None:
        """
        Initialize database connection manager and ensure schema tables exist.

        Parameters
        ----------
        db_path : Path
            File system path to the SQLite database file.
        """
        self.db_path: Path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[Connection, None, None]:
        """
        Context manager that yields a configured SQLite connection and guarantees closing.

        Yields
        ------
        Connection
            Active SQLite connection configured with WAL journal mode and Row factory.
        """
        connection: Connection = sqlite3_connect(str(self.db_path), timeout=30.0)
        connection.row_factory = Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
        finally:
            connection.close()

    def _init_db(self) -> None:
        """Initialize database tables and indexes."""
        with self._get_connection() as connection:
            cursor: Cursor = connection.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS ignored_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT UNIQUE NOT NULL,
                    item_type TEXT DEFAULT 'pattern',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS anime_series (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_path TEXT UNIQUE NOT NULL,
                    folder_name TEXT NOT NULL,
                    site_title TEXT,
                    site_session TEXT,
                    poster_url TEXT,
                    poster_downloaded INTEGER DEFAULT 0,
                    last_scanned_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS downloaded_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id INTEGER NOT NULL,
                    episode_number INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    resolution TEXT,
                    audio TEXT,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (series_id) REFERENCES anime_series(id) ON DELETE CASCADE,
                    UNIQUE (series_id, episode_number)
                );

                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    downloaded_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    notes TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_series_folder_path ON anime_series(folder_path);
                CREATE INDEX IF NOT EXISTS idx_series_folder_name ON anime_series(folder_name);
                CREATE INDEX IF NOT EXISTS idx_series_site_session ON anime_series(site_session);
                CREATE INDEX IF NOT EXISTS idx_episodes_series_ep ON downloaded_episodes(series_id, episode_number);
            """)
            connection.commit()

            # Migration: drop deprecated site_url column if still present (links can be rotated)
            columns: List[str] = [
                row[1]
                for row in connection.execute("PRAGMA table_info(anime_series)").fetchall()
            ]
            if "site_url" in columns:
                connection.executescript("""
                    CREATE TABLE anime_series_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_path TEXT UNIQUE NOT NULL,
                        folder_name TEXT NOT NULL,
                        site_title TEXT,
                        site_session TEXT,
                        poster_url TEXT,
                        poster_downloaded INTEGER DEFAULT 0,
                        last_scanned_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT INTO anime_series_new
                        SELECT id, folder_path, folder_name, site_title, site_session,
                               poster_url, poster_downloaded, last_scanned_at, created_at
                        FROM anime_series;
                    DROP TABLE anime_series;
                    ALTER TABLE anime_series_new RENAME TO anime_series;
                    CREATE INDEX IF NOT EXISTS idx_series_folder_path ON anime_series(folder_path);
                    CREATE INDEX IF NOT EXISTS idx_series_folder_name ON anime_series(folder_name);
                    CREATE INDEX IF NOT EXISTS idx_series_site_session ON anime_series(site_session);
                """)
                connection.commit()
                logger.info("Migration: dropped deprecated site_url column from anime_series")

    # Settings operations
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration setting value.

        Parameters
        ----------
        key : str
            Configuration key name.
        default : Optional[str], default=None
            Fallback value if key is not found.

        Returns
        -------
        Optional[str]
            Stored setting string value, or default.
        """
        with self._get_connection() as connection:
            row: Optional[Row] = connection.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """
        Set or update a configuration setting value.

        Parameters
        ----------
        key : str
            Configuration key name.
        value : str
            String value to store.
        """
        with self._get_connection() as connection:
            connection.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                (key, str(value)),
            )
            connection.commit()

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """
        Get a boolean setting value.

        Parameters
        ----------
        key : str
            Configuration key name.
        default : bool, default=False
            Fallback value if key is not found.

        Returns
        -------
        bool
            Parsed boolean value.
        """
        value: Optional[str] = self.get_setting(key)
        if value is None:
            return default
        return value.strip().lower() in ("1", "true", "yes", "on")

    def set_bool_setting(self, key: str, value: bool) -> None:
        """
        Set a boolean setting value.

        Parameters
        ----------
        key : str
            Configuration key name.
        value : bool
            Boolean value to store.
        """
        self.set_setting(key, "1" if value else "0")

    # Ignored items operations
    def get_ignored_items(self) -> List[str]:
        """
        Return all currently ignored patterns / names.

        Returns
        -------
        List[str]
            List of ignored pattern strings.
        """
        with self._get_connection() as connection:
            rows: List[Row] = connection.execute(
                "SELECT pattern FROM ignored_items ORDER BY id ASC"
            ).fetchall()
            return [row["pattern"] for row in rows]

    def add_ignored_items(self, patterns: List[str], item_type: str = "pattern") -> int:
        """
        Add patterns to the ignored list.

        Parameters
        ----------
        patterns : List[str]
            List of pattern strings to ignore.
        item_type : str, default="pattern"
            Descriptor for pattern classification.

        Returns
        -------
        int
            Count of newly inserted items.
        """
        added_count: int = 0
        with self._get_connection() as connection:
            for pattern in patterns:
                cleaned_pattern: str = pattern.strip()
                if not cleaned_pattern:
                    continue
                try:
                    connection.execute(
                        "INSERT OR IGNORE INTO ignored_items (pattern, item_type) VALUES (?, ?)",
                        (cleaned_pattern, item_type),
                    )
                    if connection.total_changes:
                        added_count += 1
                except SqliteError as sqlite_error:
                    logger.error(
                        f"Error adding ignored pattern '{cleaned_pattern}': {sqlite_error}"
                    )
            connection.commit()
        return added_count

    def remove_ignored_items(self, patterns: List[str]) -> List[str]:
        """
        Remove specified patterns (case-insensitive) from ignored list.

        Parameters
        ----------
        patterns : List[str]
            Patterns to match and remove.

        Returns
        -------
        List[str]
            List of pattern strings successfully removed.
        """
        removed_items: List[str] = []
        with self._get_connection() as connection:
            for pattern in patterns:
                cleaned_pattern: str = pattern.strip()
                if not cleaned_pattern:
                    continue
                row: Optional[Row] = connection.execute(
                    "SELECT pattern FROM ignored_items WHERE LOWER(pattern) = LOWER(?)",
                    (cleaned_pattern,),
                ).fetchone()
                if row:
                    removed_items.append(row["pattern"])
                    connection.execute(
                        "DELETE FROM ignored_items WHERE LOWER(pattern) = LOWER(?)",
                        (cleaned_pattern,),
                    )
            connection.commit()
        return removed_items

    def clear_ignored_items(self) -> None:
        """Clear all entries from the ignored items table."""
        with self._get_connection() as connection:
            connection.execute("DELETE FROM ignored_items")
            connection.commit()

    # Anime series & mapping operations
    def get_series_by_folder_path(self, folder_path: Path) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached series record by absolute folder path.

        Parameters
        ----------
        folder_path : Path
            Filesystem folder path to query.

        Returns
        -------
        Optional[Dict[str, Any]]
            Series record dictionary if found, None otherwise.
        """
        normalized_path: str = str(Path(folder_path).resolve()).replace("\\", "/")
        with self._get_connection() as connection:
            row: Optional[Row] = connection.execute(
                "SELECT * FROM anime_series WHERE folder_path = ?", (normalized_path,)
            ).fetchone()
            return dict(row) if row else None

    def get_series_by_id(self, series_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve series record by primary key ID.

        Parameters
        ----------
        series_id : int
            Primary key ID in anime_series.

        Returns
        -------
        Optional[Dict[str, Any]]
            Series record dictionary if found, None otherwise.
        """
        with self._get_connection() as connection:
            row: Optional[Row] = connection.execute(
                "SELECT * FROM anime_series WHERE id = ?", (series_id,)
            ).fetchone()
            return dict(row) if row else None

    def upsert_series(
        self,
        folder_path: Path,
        folder_name: str,
        site_title: Optional[str] = None,
        site_session: Optional[str] = None,
    ) -> int:
        """
        Insert or update an anime series mapping.

        Parameters
        ----------
        folder_path : Path
            Absolute path to the local anime folder.
        folder_name : str
            Local folder name of the series.
        site_title : Optional[str], default=None
            Official title resolved on Animepahe.
        site_session : Optional[str], default=None
            Session identifier on Animepahe.

        Returns
        -------
        int
            Primary key ID of the series in the database.
        """
        normalized_path: str = str(Path(folder_path).resolve()).replace("\\", "/")
        with self._get_connection() as connection:
            existing: Optional[Row] = connection.execute(
                "SELECT id FROM anime_series WHERE folder_path = ?", (normalized_path,)
            ).fetchone()

            series_id: int
            if existing:
                series_id = int(existing["id"])
                connection.execute(
                    """
                    UPDATE anime_series
                    SET folder_name = ?,
                        site_title = COALESCE(?, site_title),
                        site_session = COALESCE(?, site_session),
                        last_scanned_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (folder_name, site_title, site_session, series_id),
                )
            else:
                cursor: Cursor = connection.execute(
                    """
                    INSERT INTO anime_series (
                        folder_path, folder_name, site_title, site_session, last_scanned_at
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                    (normalized_path, folder_name, site_title, site_session),
                )
                series_id = int(cursor.lastrowid)

            connection.commit()
            return series_id

    # Downloaded episodes operations
    def record_downloaded_episode(
        self,
        series_id: int,
        episode_number: int,
        filename: str,
        resolution: str = "",
        audio: str = "",
    ) -> None:
        """
        Record a successfully downloaded episode in the database.

        Parameters
        ----------
        series_id : int
            Foreign key series ID.
        episode_number : int
            Episode number downloaded.
        filename : str
            Filename placed in the folder.
        resolution : str, default=""
            Video resolution tag.
        audio : str, default=""
            Audio track preference tag.
        """
        with self._get_connection() as connection:
            connection.execute(
                """
                INSERT INTO downloaded_episodes (
                    series_id, episode_number, filename, resolution, audio, downloaded_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(series_id, episode_number) DO UPDATE SET
                    filename = excluded.filename,
                    resolution = excluded.resolution,
                    audio = excluded.audio,
                    downloaded_at = CURRENT_TIMESTAMP
            """,
                (series_id, episode_number, filename, resolution, audio),
            )
            connection.commit()

    def get_downloaded_episodes_for_series(self, series_id: int) -> Set[int]:
        """
        Return set of episode numbers recorded as downloaded for a series.

        Parameters
        ----------
        series_id : int
            Foreign key series ID.

        Returns
        -------
        Set[int]
            Set of recorded episode numbers.
        """
        with self._get_connection() as connection:
            rows: List[Row] = connection.execute(
                "SELECT episode_number FROM downloaded_episodes WHERE series_id = ?",
                (series_id,),
            ).fetchall()
            return {row["episode_number"] for row in rows}

    def is_episode_downloaded(self, series_id: int, episode_number: int) -> bool:
        """
        Check if a specific episode number is recorded as downloaded.

        Parameters
        ----------
        series_id : int
            Foreign key series ID.
        episode_number : int
            Episode sequence number to check.

        Returns
        -------
        bool
            True if present in downloaded_episodes, False otherwise.
        """
        with self._get_connection() as connection:
            row: Optional[Row] = connection.execute(
                "SELECT 1 FROM downloaded_episodes WHERE series_id = ? AND episode_number = ?",
                (series_id, episode_number),
            ).fetchone()
            return bool(row)

    # History & logging operations
    def record_run_history(
        self, downloaded_count: int, error_count: int, notes: str = ""
    ) -> None:
        """
        Record a pipeline run summary into the history table.

        Parameters
        ----------
        downloaded_count : int
            Number of episodes downloaded during the run.
        error_count : int
            Number of errors encountered during the run.
        notes : str, default=""
            Contextual details regarding the execution.
        """
        with self._get_connection() as connection:
            connection.execute(
                """
                INSERT INTO history (run_timestamp, downloaded_count, error_count, notes)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
            """,
                (downloaded_count, error_count, notes),
            )
            # Keep only the last 100 history records
            connection.execute("""
                DELETE FROM history WHERE id NOT IN (
                    SELECT id FROM history ORDER BY id DESC LIMIT 100
                )
            """)
            connection.commit()

    # Legacy JSON migration
    def migrate_legacy_files_if_needed(
        self, state_file: Optional[Path] = None, ignored_file: Optional[Path] = None
    ) -> None:
        """
        Import data from legacy state.json and ignored.json / exceptions.json if present (runs once).

        Parameters
        ----------
        state_file : Optional[Path], default=None
            Path to legacy state.json file.
        ignored_file : Optional[Path], default=None
            Path to legacy ignored.json file.
        """
        if self.get_setting("legacy_files_migrated") == "1":
            return

        with self._get_connection() as connection:
            # 1. Migrate Ignored Items
            if ignored_file and ignored_file.exists():
                try:
                    content: str = ignored_file.read_text(encoding="utf-8")
                    ignored_data: Any = json_loads(content)
                    if isinstance(ignored_data, list):
                        items: List[str] = [
                            str(item).strip() for item in ignored_data if str(item).strip()
                        ]
                        for item in items:
                            connection.execute(
                                "INSERT OR IGNORE INTO ignored_items (pattern) VALUES (?)",
                                (item,),
                            )
                        logger.info(
                            f"Migrated {len(items)} ignored items from {ignored_file.name} to SQLite."
                        )
                except Exception as migrate_error:
                    logger.warning(
                        f"Could not migrate legacy ignored file {ignored_file}: {migrate_error}"
                    )

            # 2. Migrate State File (downloaded episodes & history)
            if state_file and state_file.exists():
                try:
                    state_content: str = state_file.read_text(encoding="utf-8")
                    state_data: Any = json_loads(state_content)
                    if isinstance(state_data, dict):
                        # Migrate downloaded episodes
                        episodes_dict: Dict[str, Any] = state_data.get("downloaded_episodes", {})
                        for folder_name, episodes_list in episodes_dict.items():
                            if not isinstance(episodes_list, list):
                                continue
                            dummy_path: str = f"D:/Videos/Anime Unwatched/{folder_name}"
                            connection.execute(
                                """
                                INSERT OR IGNORE INTO anime_series (folder_path, folder_name)
                                VALUES (?, ?)
                            """,
                                (dummy_path, folder_name),
                            )
                            cursor: Cursor = connection.execute(
                                "SELECT id FROM anime_series WHERE folder_path = ?",
                                (dummy_path,),
                            )
                            row: Optional[Row] = cursor.fetchone()
                            series_id: Optional[int] = row[0] if row else None
                            if series_id:
                                for episode_num in episodes_list:
                                    if isinstance(episode_num, int):
                                        connection.execute(
                                            """
                                            INSERT OR IGNORE INTO downloaded_episodes (series_id, episode_number, filename)
                                            VALUES (?, ?, ?)
                                        """,
                                            (
                                                series_id,
                                                episode_num,
                                                f"{folder_name} {episode_num:02d}.mp4",
                                            ),
                                        )

                        # Migrate history
                        history_list: List[Any] = state_data.get("history", [])
                        for history_item in history_list:
                            if isinstance(history_item, dict):
                                connection.execute(
                                    """
                                    INSERT INTO history (downloaded_count, error_count, notes)
                                    VALUES (?, ?, ?)
                                """,
                                    (
                                        history_item.get("downloaded", 0),
                                        history_item.get("errors", 0),
                                        history_item.get("notes", "Migrated from state.json"),
                                    ),
                                )
                        logger.info(f"Migrated legacy state from {state_file.name} to SQLite.")
                except Exception as state_error:
                    logger.warning(
                        f"Could not migrate legacy state file {state_file}: {state_error}"
                    )

            connection.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES ('legacy_files_migrated', '1')"
            )
            connection.commit()
