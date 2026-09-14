/**
 * Navigation item specification: CLI Commands Reference.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/cli-commands-reference.js"] = {
  "item_title": "CLI Commands Reference",
  "icon_name": "terminal",
  "header_container": {
    "title": "CLI Commands & Options Reference",
    "description": "Complete reference of command-line flags, automation switches, headless execution modes, and debugging utilities for main.py and kyaa.exe.",
    "badge_list": [
      { "icon_name": "code",           "badge_label": "Python main.py Core" },
      { "icon_name": "play_arrow",     "badge_label": "--start-automation-stream" },
      { "icon_name": "bug_report",     "badge_label": "--debug Headless Toggle" },
      { "icon_name": "cloud_download", "badge_label": "--download-model" }
    ],
    "mockup_card": {
      "mockup_title": "Command Terminal",
      "mockup_options": [
        "python main.py --sync",
        "python main.py --start-automation-stream",
        "python main.py --download-model",
        "python main.py --folder \"D:\\Anime\" --quality 1080p"
      ],
      "mockup_action_buttons": [
        "Copy Command",
        "Run Help"
      ],
      "mockup_image_path": "assets/settings.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "CLI Flags & Arguments",
      "icon_name": "list",
      "section_blocks": [
        {
          "heading_title": "Standalone CLI Power & Flexibility",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! can be run as a fully autonomous command-line utility on headless Windows servers, background Task Scheduler jobs, or CI/CD pipelines without ever opening the Flutter graphical interface."
        },
        {
          "heading_title": "Command-Line Flags Reference Table",
          "block_type": "table",
          "table_headers": [
            "Flag / Option",
            "Type",
            "Default",
            "Description & Usage"
          ],
          "table_rows": [
            [
              "-f, --folder <PATH>",
              "String",
              "Database Path",
              "Overrides the anime root media directory for this run."
            ],
            [
              "-s, --sync",
              "Flag",
              "False",
              "Executes a complete library synchronization pass in terminal mode."
            ],
            [
              "--start-automation-stream",
              "Flag",
              "False",
              "Emits NDJSON real-time events over stdout for Flutter IPC bridge."
            ],
            [
              "-q, --quality <RES>",
              "Enum (1080p|720p)",
              "1080p",
              "Sets requested video resolution for mirror downloads."
            ],
            [
              "-a, --audio <STREAM>",
              "Enum (sub|dub)",
              "sub",
              "Selects preferred audio stream (Japanese Sub vs English Dub)."
            ],
            [
              "--download-model",
              "Flag",
              "False",
              "Downloads the Qwen2.5-0.5B GGUF model from HuggingFace and exits."
            ],
            [
              "--debug",
              "Flag",
              "False",
              "Disables headless mode in Camoufox; opens visual browser window."
            ],
            [
              "-v, --version",
              "Flag",
              "False",
              "Outputs current version of Kyaa!! Anime Refresher."
            ]
          ]
        },
        {
          "heading_title": "Standard CLI Usage Examples",
          "block_type": "code_block",
          "header_label": "PowerShell \u2022 CLI Commands",
          "language_identifier": "powershell",
          "code_content": "# 1. Run terminal sync with live progress bars\npython main.py --sync --folder \"D:\\Anime\"\n\n# 2. Download 720p English dubs for bandwidth saving\npython main.py --sync --quality 720p --audio dub\n\n# 3. Debug scraping with visible Camoufox browser\npython main.py --sync --debug\n\n# 4. Fetch the AI episode parsing weights\npython main.py --download-model"
        }
      ]
    },
    {
      "tab_title": "Terminal vs Stream Mode",
      "icon_name": "compare_arrows",
      "section_blocks": [
        {
          "heading_title": "Comparing Execution Modes",
          "block_type": "paragraph",
          "paragraph_text": "The Python backend behaves differently depending on whether it is running as an interactive command-line application or as a child process of the Flutter frontend."
        },
        {
          "heading_title": "Terminal Mode vs NDJSON Stream Mode",
          "block_type": "table",
          "table_headers": [
            "Feature",
            "Interactive Terminal (--sync)",
            "NDJSON Stream Mode (--start-automation-stream)"
          ],
          "table_rows": [
            [
              "Target Consumer",
              "Human developer or server admin",
              "Flutter CliBridgeService (Dart)"
            ],
            [
              "Output Format",
              "ANSI escape colors and rich progress bars",
              "Structured single-line JSON objects"
            ],
            [
              "Logging Verbosity",
              "Pretty-printed console logs",
              "Packaged inside JSON error log fields"
            ],
            [
              "Process Signal Handling",
              "Standard Ctrl+C interrupts gracefully",
              "SIGINT/SIGTERM cleanly halts active sockets"
            ]
          ]
        },
        {
          "heading_title": "Key CLI Operational Guidelines",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Path Quotes in PowerShell:",
              "item_description": "Always wrap folder paths containing spaces in double quotes: --folder \"D:\\My Anime Library\"."
            },
            {
              "highlighted_prefix": "Exit Codes:",
              "item_description": "Returns code 0 on clean sync completion, code 1 on configuration error, and code 2 on circuit breaker trip."
            },
            {
              "highlighted_prefix": "Headless Server Deployment:",
              "item_description": "Works out of the box on Windows Server 2022 / Core with no desktop display session required."
            }
          ]
        }
      ]
    }
  ]
};
