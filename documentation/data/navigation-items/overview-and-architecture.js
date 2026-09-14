/**
 * Navigation item specification: Overview & Architecture.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/overview-and-architecture.js"] = {
  "item_title": "Overview & Architecture",
  "icon_name": "hub",
  "header_container": {
    "title": "Kyaa!! Architecture & Philosophy",
    "description": "An architectural breakdown of the dual-process synchronization engine, IPC streaming protocol, stealth web scraping layer, and local AI episode parsing pipeline.",
    "badge_list": [
      { "icon_name": "devices",    "badge_label": "Flutter + Python IPC" },
      { "icon_name": "shield",     "badge_label": "Camoufox Anti-Detect" },
      { "icon_name": "database",   "badge_label": "SQLite3 State Storage" },
      { "icon_name": "psychology", "badge_label": "Qwen2.5-0.5B GGUF" }
    ],
    "mockup_card": {
      "mockup_title": "Dual-Process Architecture",
      "mockup_options": [
        "1. Flutter UI (Desktop Viewport)",
        "2. Subprocess IPC (NDJSON Stream)",
        "3. Camoufox Headless Browser Engine"
      ],
      "mockup_action_buttons": [
        "Run Sync",
        "View Stream"
      ],
      "mockup_image_path": "assets/tasks.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Architecture",
      "icon_name": "account_tree",
      "section_blocks": [
        {
          "heading_title": "System Architecture & Dual-Process Design",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! Anime Refresher is structured as a decoupled, dual-process desktop application. The frontend is built on Flutter 3.22+ Desktop for Windows, delivering a frameless, 60fps AMOLED Dark user interface. The backend is an autonomous Python engine running in a background subprocess. The two layers communicate asynchronously via high-throughput NDJSON event streams over standard I/O pipes (stdout/stderr)."
        },
        {
          "heading_title": "Visual Dashboard & Active Tasks View",
          "block_type": "image",
          "image_path": "assets/tasks.png",
          "alt_text": "Tasks tab showing active episode downloads and real-time streaming metrics",
          "caption_text": "Figure 1: Tasks View rendering live episode progress, transfer speeds in MB/s, and status badges."
        },
        {
          "heading_title": "Core Architectural Pillars",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Reactive Subprocess IPC:",
              "item_description": "The Flutter CliBridgeService spawns the Python backend in streaming mode (main.py --start-automation-stream). Real-time events are emitted as JSON lines and parsed into reactive Dart ValueNotifiers."
            },
            {
              "highlighted_prefix": "Anti-Detect Stealth Scraping:",
              "item_description": "Scrapes episode catalogs and resolves video streams using Camoufox with native humanized bezier cursor interpolation, bypassing Cloudflare Turnstile without external paid proxy solvers."
            },
            {
              "highlighted_prefix": "Autonomous Circuit Breaker:",
              "item_description": "Monitors consecutive network and catalog failures. If two or more series fail consecutively, the engine pauses, cools down for 30s, purges cookies, and rotates across mirrors (.pw, .org, .com, .ru)."
            },
            {
              "highlighted_prefix": "Dual-Engine Episode Parser:",
              "item_description": "Pairs a sub-millisecond deterministic regex pre-filter with a local quantized Qwen2.5-0.5B GGUF LLM for extracting anime titles, season indices, and episode numbers."
            },
            {
              "highlighted_prefix": "SafetyGuard File Integrity:",
              "item_description": "Pre-scan directory snapshots verify target storage folders before any write operations occur, ensuring zero unintended deletions or overwrites in your library."
            }
          ]
        },
        {
          "heading_title": "Component Stack Breakdown",
          "block_type": "table",
          "table_headers": [
            "Subsystem",
            "Technology / Framework",
            "Role & Responsibility",
            "Execution Mode"
          ],
          "table_rows": [
            [
              "Frontend Desktop App",
              "Flutter 3.22 (Dart 3.4)",
              "Frameless window, 4 viewports, theme engine, reactive progress",
              "UI Thread / Win32 Native"
            ],
            [
              "Subprocess Bridge",
              "CliBridgeService & SubprocessService",
              "Process lifecycle, NDJSON parser, command dispatcher, scheduler",
              "Async Dart Event Loop"
            ],
            [
              "Scraping & Downloader",
              "Camoufox (Firefox Dev) + Playwright",
              "Stealth browsing, Cloudflare Turnstile clearance, Kwik streaming",
              "Python AsyncIO"
            ],
            [
              "Filename Parsing",
              "Regex Heuristics + llama.cpp (Qwen2.5)",
              "Multi-token episode number & season detection",
              "Local CPU Inference"
            ],
            [
              "State Storage",
              "SQLite3 (WAL Mode)",
              "Series index, episode histories, settings, and ignore rules",
              "Atomic Transactions"
            ]
          ]
        }
      ]
    },
    {
      "tab_title": "IPC Protocol",
      "icon_name": "sync_alt",
      "section_blocks": [
        {
          "heading_title": "NDJSON Real-Time Event Protocol",
          "block_type": "paragraph",
          "paragraph_text": "When invoked with --start-automation-stream, the Python backend formats all pipeline updates into strongly-typed single-line JSON objects printed to stdout. The Flutter UI listens on stdout, converts each line into a TaskItemData model, and updates the task list in real time without polling."
        },
        {
          "heading_title": "Sample Stream Event Payload",
          "block_type": "code_block",
          "header_label": "JSON \u2022 stdout line",
          "language_identifier": "json",
          "code_content": "{\n  \"string_event\": \"download_update\",\n  \"string_timestamp\": \"2026-09-14T10:30:00Z\",\n  \"string_anime_name\": \"Solo Leveling\",\n  \"int_episode_number\": 12,\n  \"string_filename\": \"Solo Leveling 12.mp4\",\n  \"string_download_status\": \"in-progress\",\n  \"float_progress_percentage\": 68.5,\n  \"int_downloaded_bytes\": 985600000,\n  \"int_total_bytes\": 1438000000,\n  \"float_speed_mbps\": 16.4,\n  \"string_short_error_message\": \"\",\n  \"string_error_log_message\": \"\"\n}"
        },
        {
          "heading_title": "Supported Event Categories & Status Values",
          "block_type": "table",
          "table_headers": [
            "Event (string_event)",
            "Status (string_download_status)",
            "Description"
          ],
          "table_rows": [
            [
              "download_update",
              "queue",
              "Episode has been queued for download in the current series batch."
            ],
            [
              "download_update",
              "in-progress",
              "Chunked video streaming is actively transferring with progress and speed metrics."
            ],
            [
              "download_update",
              "completed",
              "File has been downloaded, verified, and renamed to the target library location."
            ],
            [
              "download_update",
              "failed",
              "Download or catalog resolution failed. Error traceback is captured in error log field."
            ]
          ]
        }
      ]
    }
  ]
};
