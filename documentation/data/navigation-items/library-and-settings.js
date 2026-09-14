/**
 * Navigation item specification: Library & Settings.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/library-and-settings.js"] = {
  "item_title": "Library & Settings",
  "icon_name": "settings",
  "header_container": {
    "title": "Library Management & Configuration",
    "description": "Configure your root anime storage paths, resolution and language preferences, download AI parsing models, and manage dynamic series exclusion chip lists.",
    "badge_list": [
      { "icon_name": "folder",       "badge_label": "Folder Picker" },
      { "icon_name": "high_quality", "badge_label": "1080p / 720p Selection" },
      { "icon_name": "subtitles",    "badge_label": "Sub / Dub Audio Stream" },
      { "icon_name": "block",        "badge_label": "Ignored Anime Chips" }
    ],
    "mockup_card": {
      "mockup_title": "Settings Viewport",
      "mockup_options": [
        "1. Anime Target Folder Picker",
        "2. Quality & Audio Stream Pills",
        "3. AI Model Downloader (Qwen2.5)",
        "4. Ignored Anime Exclusion Chips"
      ],
      "mockup_action_buttons": [
        "Browse Folder",
        "Download AI Model"
      ],
      "mockup_image_path": "assets/settings.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Settings Sections",
      "icon_name": "tune",
      "section_blocks": [
        {
          "heading_title": "Settings Dashboard Overview",
          "block_type": "paragraph",
          "paragraph_text": "The Settings tab provides a unified control panel for configuring how Kyaa!! interacts with your local filesystem, network mirrors, and scraping heuristics. All settings are validated and persisted atomically in the SQLite3 configuration database."
        },
        {
          "heading_title": "Settings Screen Visual Layout",
          "block_type": "image",
          "image_path": "assets/settings.png",
          "alt_text": "Settings view showing folder path picker, quality selector, and ignored anime chip list",
          "caption_text": "Figure 4: The Settings View with Folder Selector, Quality / Audio Pills, AI Downloader, and Ignored Anime chips."
        },
        {
          "heading_title": "Detailed Section Breakdown",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Section 1 \u2014 Target Library Folder:",
              "item_description": "Displays the current root folder path (e.g., 'D:\\Anime'). Clicking 'Browse' summons the native Win32 directory selector. When selected, the path is validated for read/write access immediately."
            },
            {
              "highlighted_prefix": "Section 2 \u2014 Quality & Audio Stream Preferences:",
              "item_description": "Custom selectable pills allow you to lock your preferred download resolution (1080p Full HD vs 720p HD) and audio stream (Subtitled Japanese with soft/hard subs vs English Dubbed)."
            },
            {
              "highlighted_prefix": "Section 3 \u2014 AI Episode Parser Model:",
              "item_description": "Displays the status of the local Qwen2.5-0.5B-Instruct-GGUF model. If missing, a single click on 'Download Model' streams the ~398MB quantized weights directly from HuggingFace with a progress bar."
            },
            {
              "highlighted_prefix": "Section 4 \u2014 Scraping & Mirror Thresholds:",
              "item_description": "Configures mirror timeout ceilings, maximum retry counts, and consecutive failure circuit-breaker thresholds before automatic mirror failover."
            },
            {
              "highlighted_prefix": "Section 5 \u2014 Ignored Anime Exclusion Chips:",
              "item_description": "A dynamic chip-tagging container where users can type anime titles or franchise names to exclude them permanently from synchronization passes. Chips can be deleted with a single click."
            }
          ]
        },
        {
          "heading_title": "Configuration Keys & Default Behaviors",
          "block_type": "table",
          "table_headers": [
            "Setting Key",
            "Data Type",
            "Default Value",
            "Behavioral Description"
          ],
          "table_rows": [
            [
              "target_folder",
              "String (Path)",
              "Empty",
              "Root media library folder where anime series directories reside."
            ],
            [
              "preferred_quality",
              "Enum (1080p | 720p)",
              "1080p",
              "Requested video resolution for mirror stream extraction."
            ],
            [
              "audio_preference",
              "Enum (sub | dub)",
              "sub",
              "Preferred audio track / stream type."
            ],
            [
              "use_ai_parser",
              "Boolean",
              "True (if model exists)",
              "Enables LLM inference fallback when regex heuristic confidence is low."
            ],
            [
              "ignored_anime",
              "JSON Array (Strings)",
              "[]",
              "List of folder or anime names to bypass during catalog discovery."
            ]
          ]
        }
      ]
    },
    {
      "tab_title": "Persistence & Safety",
      "icon_name": "storage",
      "section_blocks": [
        {
          "heading_title": "Atomic SQLite3 Storage",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! stores all preferences in an embedded SQLite3 database (%LOCALAPPDATA%\\Kyaa\\kyaa.db) using Write-Ahead Logging (WAL). Even if the process is terminated abruptly or the power cuts out, your library preferences and ignored series are never corrupted."
        },
        {
          "heading_title": "Settings Database Schema",
          "block_type": "code_block",
          "header_label": "SQL \u2022 kyaa.db",
          "language_identifier": "sql",
          "code_content": "CREATE TABLE IF NOT EXISTS settings (\n  key TEXT PRIMARY KEY NOT NULL,\n  value TEXT NOT NULL,\n  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);\n\nCREATE TABLE IF NOT EXISTS ignored_anime (\n  id INTEGER PRIMARY KEY AUTOINCREMENT,\n  anime_title TEXT NOT NULL UNIQUE,\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);"
        },
        {
          "heading_title": "SafetyGuard Pre-Scan Verification",
          "block_type": "paragraph",
          "paragraph_text": "Before any download or file renaming process starts, the backend executes SafetyGuard. It inspects the target folder to verify that it does not point to a critical operating system directory (such as C:\\Windows or %SystemRoot%) and confirms that sufficient disk capacity exists before downloading multi-gigabyte video streams."
        }
      ]
    }
  ]
};
