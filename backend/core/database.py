import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("anime_refresher.database")

class DatabaseManager:
    """Thread-safe SQLite3 database manager for Anime Refresher state, cache, and settings."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager that yields a configured SQLite connection and guarantees closing."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
        finally:
            conn.close()


    def _init_db(self) -> None:
        """Initializes database tables and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
            conn.commit()

            # Migration: drop deprecated site_url column if still present (links can be rotated)
            cols = [row[1] for row in conn.execute("PRAGMA table_info(anime_series)").fetchall()]
            if "site_url" in cols:
                conn.executescript("""
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
                conn.commit()
                logger.info("Migration: dropped deprecated site_url column from anime_series")


    # SETTINGS OPERATIONS
    # =========================================================================
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Gets a configuration setting value."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Sets or updates a configuration setting value."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                (key, str(value))
            )
            conn.commit()

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """Gets a boolean setting value."""
        val = self.get_setting(key)
        if val is None:
            return default
        return val.strip().lower() in ("1", "true", "yes", "on")

    def set_bool_setting(self, key: str, value: bool) -> None:
        """Sets a boolean setting value."""
        self.set_setting(key, "1" if value else "0")

    # =========================================================================
    # IGNORED ITEMS OPERATIONS
    # =========================================================================
    def get_ignored_items(self) -> List[str]:
        """Returns all currently ignored patterns / names."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT pattern FROM ignored_items ORDER BY id ASC").fetchall()
            return [r["pattern"] for r in rows]

    def add_ignored_items(self, patterns: List[str], item_type: str = "pattern") -> int:
        """Adds patterns to the ignored list. Returns count of newly inserted items."""
        added = 0
        with self._get_connection() as conn:
            for pat in patterns:
                clean = pat.strip()
                if not clean:
                    continue
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO ignored_items (pattern, item_type) VALUES (?, ?)",
                        (clean, item_type)
                    )
                    if conn.total_changes:
                        added += 1
                except sqlite3.Error as e:
                    logger.error(f"Error adding ignored pattern '{clean}': {e}")
            conn.commit()
        return added

    def remove_ignored_items(self, patterns: List[str]) -> List[str]:
        """Removes specified patterns (case-insensitive) from ignored list. Returns removed items."""
        removed = []
        with self._get_connection() as conn:
            for pat in patterns:
                clean = pat.strip()
                if not clean:
                    continue
                row = conn.execute("SELECT pattern FROM ignored_items WHERE LOWER(pattern) = LOWER(?)", (clean,)).fetchone()
                if row:
                    removed.append(row["pattern"])
                    conn.execute("DELETE FROM ignored_items WHERE LOWER(pattern) = LOWER(?)", (clean,))
            conn.commit()
        return removed

    def clear_ignored_items(self) -> None:
        """Clears all entries from the ignored items table."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM ignored_items")
            conn.commit()

    # =========================================================================
    # ANIME SERIES & MAPPING OPERATIONS
    # =========================================================================
    def get_series_by_folder_path(self, folder_path: Path) -> Optional[Dict[str, Any]]:
        """Retrieves cached series record by absolute folder path."""
        norm_path = str(Path(folder_path).resolve()).replace("\\", "/")
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM anime_series WHERE folder_path = ?", (norm_path,)).fetchone()
            return dict(row) if row else None

    def get_series_by_id(self, series_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves series record by primary key ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM anime_series WHERE id = ?", (series_id,)).fetchone()
            return dict(row) if row else None

    def upsert_series(
        self,
        folder_path: Path,
        folder_name: str,
        site_title: Optional[str] = None,
        site_session: Optional[str] = None
    ) -> int:
        """Inserts or updates an anime series mapping. Returns series ID."""
        norm_path = str(Path(folder_path).resolve()).replace("\\", "/")
        with self._get_connection() as conn:
            existing = conn.execute("SELECT id FROM anime_series WHERE folder_path = ?", (norm_path,)).fetchone()

            if existing:
                series_id = existing["id"]
                conn.execute("""
                    UPDATE anime_series
                    SET folder_name = ?,
                        site_title = COALESCE(?, site_title),
                        site_session = COALESCE(?, site_session),
                        last_scanned_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (folder_name, site_title, site_session, series_id))
            else:
                cursor = conn.execute("""
                    INSERT INTO anime_series (
                        folder_path, folder_name, site_title, site_session, last_scanned_at
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (norm_path, folder_name, site_title, site_session))
                series_id = cursor.lastrowid

            conn.commit()
            return series_id

    # =========================================================================
    # DOWNLOADED EPISODES OPERATIONS
    # =========================================================================
    def record_downloaded_episode(
        self,
        series_id: int,
        episode_number: int,
        filename: str,
        resolution: str = "",
        audio: str = ""
    ) -> None:
        """Records a successfully downloaded episode in the database."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO downloaded_episodes (
                    series_id, episode_number, filename, resolution, audio, downloaded_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(series_id, episode_number) DO UPDATE SET
                    filename = excluded.filename,
                    resolution = excluded.resolution,
                    audio = excluded.audio,
                    downloaded_at = CURRENT_TIMESTAMP
            """, (series_id, episode_number, filename, resolution, audio))
            conn.commit()

    def get_downloaded_episodes_for_series(self, series_id: int) -> Set[int]:
        """Returns set of episode numbers recorded as downloaded for a series."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT episode_number FROM downloaded_episodes WHERE series_id = ?", (series_id,)).fetchall()
            return {r["episode_number"] for r in rows}

    def is_episode_downloaded(self, series_id: int, episode_number: int) -> bool:
        """Checks if a specific episode number is recorded as downloaded."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM downloaded_episodes WHERE series_id = ? AND episode_number = ?",
                (series_id, episode_number)
            ).fetchone()
            return bool(row)

    # =========================================================================
    # HISTORY & LOGGING OPERATIONS
    # =========================================================================
    def record_run_history(self, downloaded_count: int, error_count: int, notes: str = "") -> None:
        """Records a pipeline run summary into the history table."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO history (run_timestamp, downloaded_count, error_count, notes)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
            """, (downloaded_count, error_count, notes))
            # Keep only the last 100 history records
            conn.execute("""
                DELETE FROM history WHERE id NOT IN (
                    SELECT id FROM history ORDER BY id DESC LIMIT 100
                )
            """)
            conn.commit()

    # =========================================================================
    # LEGACY JSON MIGRATION
    # =========================================================================
    def migrate_legacy_files_if_needed(self, state_file: Optional[Path] = None, ignored_file: Optional[Path] = None) -> None:
        """Imports data from legacy state.json and ignored.json / exceptions.json if present (runs once)."""
        if self.get_setting("legacy_files_migrated") == "1":
            return

        with self._get_connection() as conn:
            # 1. Migrate Ignored Items
            if ignored_file and ignored_file.exists():
                try:
                    content = ignored_file.read_text(encoding="utf-8")
                    data = json.loads(content)
                    if isinstance(data, list):
                        items = [str(x).strip() for x in data if str(x).strip()]
                        for item in items:
                            conn.execute("INSERT OR IGNORE INTO ignored_items (pattern) VALUES (?)", (item,))
                        logger.info(f"Migrated {len(items)} ignored items from {ignored_file.name} to SQLite.")
                except Exception as e:
                    logger.warning(f"Could not migrate legacy ignored file {ignored_file}: {e}")

            # 2. Migrate State File (downloaded episodes & history)
            if state_file and state_file.exists():
                try:
                    content = state_file.read_text(encoding="utf-8")
                    data = json.loads(content)
                    if isinstance(data, dict):
                        # Migrate downloaded episodes
                        episodes_dict = data.get("downloaded_episodes", {})
                        for folder_name, eps in episodes_dict.items():
                            if not isinstance(eps, list):
                                continue
                            dummy_path = f"D:/Videos/Anime Unwatched/{folder_name}"
                            conn.execute("""
                                INSERT OR IGNORE INTO anime_series (folder_path, folder_name)
                                VALUES (?, ?)
                            """, (dummy_path, folder_name))
                            cur = conn.execute("SELECT id FROM anime_series WHERE folder_path = ?", (dummy_path,))
                            row = cur.fetchone()
                            series_id = row[0] if row else None
                            if series_id:
                                for ep in eps:
                                    if isinstance(ep, int):
                                        conn.execute("""
                                            INSERT OR IGNORE INTO episodes (series_id, episode_number, filename)
                                            VALUES (?, ?, ?)
                                        """, (series_id, ep, f"{folder_name} {ep:02d}.mp4"))

                        # Migrate history
                        history_list = data.get("history", [])
                        for h in history_list:
                            if isinstance(h, dict):
                                conn.execute("""
                                    INSERT INTO history (downloaded_count, error_count, notes)
                                    VALUES (?, ?, ?)
                                """, (
                                    h.get("downloaded", 0),
                                    h.get("errors", 0),
                                    h.get("notes", "Migrated from state.json")
                                ))
                        logger.info(f"Migrated legacy state from {state_file.name} to SQLite.")
                except Exception as e:
                    logger.warning(f"Could not migrate legacy state file {state_file}: {e}")

            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('legacy_files_migrated', '1')")
            conn.commit()
