/**
 * Navigation item specification: Tasks & Live Streaming.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/tasks-and-live-streaming.js"] = {
  "item_title": "Tasks & Live Streaming",
  "icon_name": "stream",
  "header_container": {
    "title": "Tasks View & NDJSON Live Streaming",
    "description": "Real-time task monitoring powered by non-blocking NDJSON subprocess events, displaying transfer speeds, byte counters, smooth progress bars, and diagnostics modals.",
    "badge_list": [
      { "icon_name": "sync",        "badge_label": "NDJSON Stream" },
      { "icon_name": "speed",       "badge_label": "Live MB/s Metrics" },
      { "icon_name": "bug_report",  "badge_label": "Error Traceback Modal" },
      { "icon_name": "hourglass_empty", "badge_label": "Queue Lifecycle" }
    ],
    "mockup_card": {
      "mockup_title": "Active Task Cards",
      "mockup_options": [
        "Transferred: 985.6 MB / 1.43 GB",
        "Speed: 16.4 MB/s (Direct Kwik Stream)",
        "Status: In Progress",
        "Error Traceback Modal"
      ],
      "mockup_action_buttons": [
        "Clear Completed",
        "Cancel Active"
      ],
      "mockup_image_path": "assets/tasks.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Tasks UI & Metrics",
      "icon_name": "dashboard",
      "section_blocks": [
        {
          "heading_title": "Real-Time Task Monitoring Viewport",
          "block_type": "paragraph",
          "paragraph_text": "The Tasks tab is the operational command center of Kyaa!! Anime Refresher. Unlike conventional download managers that poll a backend database every few seconds, Kyaa!! updates its UI reactively via an asynchronous NDJSON event stream with sub-millisecond dispatch times."
        },
        {
          "heading_title": "Live Task Dashboard Screenshot",
          "block_type": "image",
          "image_path": "assets/tasks.png",
          "alt_text": "Tasks tab showing active episode downloads with speed and percentage indicators",
          "caption_text": "Figure 3: Tasks tab displaying in-progress downloads, transfer rates, queued items, and status indicators."
        },
        {
          "heading_title": "Task Card Anatomy & Components",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Header & Episode Badge:",
              "item_description": "Displays the sanitized anime series title alongside an accent-colored pill displaying the exact detected episode number (e.g., 'EP 12')."
            },
            {
              "highlighted_prefix": "Reactive Progress Bar:",
              "item_description": "Renders an indeterminate animated glow while Camoufox navigates mirrors and extracts Kwik stream keys, transitioning smoothly to a determinate percentage bar during video chunk transfers."
            },
            {
              "highlighted_prefix": "Throughput & Size Counters:",
              "item_description": "Displays live bytes transferred over total expected bytes (e.g., '985.6 MB / 1.43 GB') with instantaneous transfer velocity calculated in megabytes per second (MB/s)."
            },
            {
              "highlighted_prefix": "Status Indicator & Error Modal:",
              "item_description": "Badges indicate Queued (grey), In Progress (blue/primary), Completed (green), or Failed (red). Clicking any failed badge opens an inspection dialog containing full stack traces and diagnostic logs."
            }
          ]
        },
        {
          "heading_title": "Task Lifecycle State Machine",
          "block_type": "table",
          "table_headers": [
            "Lifecycle State",
            "Visual Indicator",
            "Engine Activity",
            "User Action"
          ],
          "table_rows": [
            [
              "queued",
              "Grey Pill with Clock Icon",
              "Series matched; awaiting worker thread slot",
              "Cancel or re-order"
            ],
            [
              "resolving",
              "Pulsing Pill with Search Icon",
              "Camoufox navigating mirrors and solving Turnstile",
              "View debug browser logs"
            ],
            [
              "in-progress",
              "Cyan Pill with Speed Counter",
              "Direct chunked socket streaming from Kwik CDN",
              "Pause / Terminate stream"
            ],
            [
              "completed",
              "Green Pill with Checkmark",
              "Atomic move to final target folder and DB save",
              "Open directory in Explorer"
            ],
            [
              "failed",
              "Red Pill with Warning Icon",
              "Mirror timeout or 403 Forbidden; circuit breaker tripped",
              "Click to view full traceback"
            ]
          ]
        }
      ]
    },
    {
      "tab_title": "NDJSON Streaming Protocol",
      "icon_name": "network_check",
      "section_blocks": [
        {
          "heading_title": "Subprocess Streaming Architecture",
          "block_type": "paragraph",
          "paragraph_text": "The Flutter UI communicates with the Python core through CliBridgeService, which wraps Dart's Process.start(). The Python process is invoked with --start-automation-stream, instructing it to emit one JSON payload per event line on stdout. Dart's utf8.decoder and LineSplitter parse each line asynchronously into strongly-typed TaskItemData records."
        },
        {
          "heading_title": "Event Data Schema & Dart Ingestion",
          "block_type": "code_block",
          "header_label": "Dart \u2022 TaskItemData Parser",
          "language_identifier": "dart",
          "code_content": "void _handleProcessLine(String line) {\n  if (!line.startsWith('{')) return;\n  try {\n    final jsonMap = jsonDecode(line) as Map<String, dynamic>;\n    final eventType = jsonMap['string_event'] as String?;\n    \n    if (eventType == 'download_update') {\n      final task = TaskItemData.fromJson(jsonMap);\n      _updateOrInsertTask(task);\n    }\n  } catch (e) {\n    debugPrint('Failed to parse NDJSON line: $e');\n  }\n}"
        },
        {
          "heading_title": "Error Diagnosis & Traceback Handling",
          "block_type": "paragraph",
          "paragraph_text": "When a network or parsing failure happens inside the Python backend, the complete traceback is captured and packaged into the string_error_log_message field. The Flutter UI provides a copyable dialog allowing users to report issues directly to GitHub."
        },
        {
          "heading_title": "Error Event Payload Example",
          "block_type": "code_block",
          "header_label": "JSON \u2022 stdout line on failure",
          "language_identifier": "json",
          "code_content": "{\n  \"string_event\": \"download_update\",\n  \"string_timestamp\": \"2026-09-14T10:32:15Z\",\n  \"string_anime_name\": \"Tower of God S2\",\n  \"int_episode_number\": 8,\n  \"string_download_status\": \"failed\",\n  \"float_progress_percentage\": 0.0,\n  \"string_short_error_message\": \"CamoufoxTurnstileTimeout: 403 Cloudflare Challenge\",\n  \"string_error_log_message\": \"Traceback (most recent call last):\\n  File 'scraper.py', line 142, in solve_stream\\n    await page.wait_for_selector('.kwik-download', timeout=30000)\\nPlaywrightTimeoutError: Timeout 30000ms exceeded.\"\n}"
        }
      ]
    }
  ]
};
