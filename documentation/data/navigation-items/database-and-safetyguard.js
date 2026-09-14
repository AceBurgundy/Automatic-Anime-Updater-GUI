/**
 * Navigation item specification: Database & SafetyGuard.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/database-and-safetyguard.js"] = {
  "item_title": "Database & SafetyGuard",
  "icon_name": "database",
  "header_container": {
    "title": "SQLite3 Storage & SafetyGuard Engine",
    "description": "High-performance ACID state persistence with sub-millisecond legacy migration and pre-scan filesystem snapshot safeguards to prevent library corruption.",
    "badge_list": [
      { "icon_name": "storage",      "badge_label": "SQLite3 WAL Mode" },
      { "icon_name": "security",     "badge_label": "SafetyGuard Pre-Scan" },
      { "icon_name": "fast_forward", "badge_label": "< 0.001s Atomic Migration" },
      { "icon_name": "history",      "badge_label": "Indexed Episode History" }
    ],
    "mockup_card": {
      "mockup_title": "State & Integrity",
      "mockup_options": [
        "1. Database: kyaa.db (WAL Enabled)",
        "2. SafetyGuard: 0 Overwrite Violations",
        "3. Legacy Config: Migrated in 0.8ms",
        "4. Integrity Check: PRAGMA OK"
      ],
      "mockup_action_buttons": [
        "Run Integrity Check",
        "Backup Database"
      ],
      "mockup_image_path": "assets/settings.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Database Architecture",
      "icon_name": "dataset",
      "section_blocks": [
        {
          "heading_title": "Relational Storage with SQLite3",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! stores all application state, episode download histories, mirror mappings, and user preferences in an embedded SQLite3 database. By activating Write-Ahead Logging (PRAGMA journal_mode=WAL;), the Python backend can perform concurrent batch inserts while the Flutter UI reads without lock contention."
        },
        {
          "heading_title": "Database Schema Definition",
          "block_type": "code_block",
          "header_label": "SQL \u2022 kyaa.db Schema",
          "language_identifier": "sql",
          "code_content": "-- Series Master Table\nCREATE TABLE IF NOT EXISTS anime_series (\n  id INTEGER PRIMARY KEY AUTOINCREMENT,\n  title TEXT NOT NULL UNIQUE,\n  folder_path TEXT NOT NULL,\n  mirror_session_id TEXT,\n  total_episodes_found INTEGER DEFAULT 0,\n  last_scanned_at TIMESTAMP\n);\n\n-- Downloaded Episode Records\nCREATE TABLE IF NOT EXISTS episodes (\n  id INTEGER PRIMARY KEY AUTOINCREMENT,\n  series_id INTEGER NOT NULL REFERENCES anime_series(id),\n  episode_number REAL NOT NULL,\n  filename TEXT NOT NULL,\n  file_size_bytes INTEGER,\n  quality TEXT DEFAULT '1080p',\n  downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n  UNIQUE(series_id, episode_number)\n);\n\n-- Key-Value Settings\nCREATE TABLE IF NOT EXISTS settings (\n  key TEXT PRIMARY KEY NOT NULL,\n  value TEXT NOT NULL,\n  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);"
        },
        {
          "heading_title": "Sub-Millisecond Legacy Migration",
          "block_type": "paragraph",
          "paragraph_text": "If you upgrade from older versions of Kyaa!! or Python Material Dialogs scripts that stored configuration in flat JSON files, the backend automatically detects the legacy file, executes a sub-millisecond (< 0.001s) atomic transaction into SQLite, and archives the old JSON safely."
        },
        {
          "heading_title": "Database Storage Advantages",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "ACID Compliance:",
              "item_description": "Guarantees zero database corruption even during abrupt power loss or operating system restarts."
            },
            {
              "highlighted_prefix": "Instant Duplicate Detection:",
              "item_description": "Unique constraints on (series_id, episode_number) ensure the scraper never attempts to download an episode that already exists in your library."
            },
            {
              "highlighted_prefix": "Compact Footprint:",
              "item_description": "A comprehensive anime library tracking over 500 series and 10,000 episodes occupies less than 4 megabytes of disk space."
            }
          ]
        }
      ]
    },
    {
      "tab_title": "SafetyGuard Engine",
      "icon_name": "shield",
      "section_blocks": [
        {
          "heading_title": "SafetyGuard File Integrity Protocol",
          "block_type": "paragraph",
          "paragraph_text": "SafetyGuard is Kyaa's defensive runtime system designed to prevent file corruption, accidental overwrites, or dangerous directory scans on the host computer."
        },
        {
          "heading_title": "SafetyGuard Protection Mechanisms",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Pre-Scan Snapshotting:",
              "item_description": "Before scanning or writing files, SafetyGuard indexes the exact file sizes and directory layout. Any discrepancies immediately abort the batch."
            },
            {
              "highlighted_prefix": "Atomic .part Staging:",
              "item_description": "Incoming video chunks are written to temporary staging files (e.g. 'Solo Leveling 12.mp4.part'). Only upon full download completion and header validation is the file atomically renamed to .mp4."
            },
            {
              "highlighted_prefix": "System Directory Blacklist:",
              "item_description": "Refuses to run if the selected anime folder is an OS directory (e.g. C:\\, C:\\Windows, C:\\Program Files, %APPDATA%)."
            },
            {
              "highlighted_prefix": "Disk Headroom Enforcement:",
              "item_description": "Monitors target drive free space; halts downloads automatically if free space drops below 2.0 GB to prevent system disk freezes."
            }
          ]
        },
        {
          "heading_title": "SafetyGuard Verification Checkpoints",
          "block_type": "table",
          "table_headers": [
            "Checkpoint",
            "Timing",
            "Condition Verified",
            "Action if Failed"
          ],
          "table_rows": [
            [
              "Path Sanitation",
              "On Settings Save",
              "Valid path; not a system directory",
              "Rejects setting; alerts user in UI"
            ],
            [
              "Disk Headroom",
              "Pre-Download",
              "Target drive has \u2265 2.0 GB free space",
              "Pauses queue; emits disk alert"
            ],
            [
              "Stream Validation",
              "Post-Download",
              "File size matches Content-Length header",
              "Deletes .part file; retries stream"
            ],
            [
              "Atomic Rename",
              "Final Step",
              "No locked handles on destination file",
              "Performs instant Win32 MoveFileEx"
            ]
          ]
        }
      ]
    }
  ]
};
