/**
 * Navigation item specification: Quickstart & Usage.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/quickstart-and-usage.js"] = {
  "item_title": "Quickstart & Usage",
  "icon_name": "rocket_launch",
  "header_container": {
    "title": "Quickstart & Usage Walkthrough",
    "description": "A comprehensive step-by-step walkthrough to configure your anime library directory, set download preferences, trigger synchronization, and track live episode streams.",
    "badge_list": [
      { "icon_name": "folder_open",          "badge_label": "Directory Selection" },
      { "icon_name": "play_circle",         "badge_label": "One-Click Sync" },
      { "icon_name": "speed",               "badge_label": "Real-Time Tracking" },
      { "icon_name": "notifications_active", "badge_label": "Desktop Alerts" }
    ],
    "mockup_card": {
      "mockup_title": "Daily Sync Routine",
      "mockup_options": [
        "1. Select Root Anime Folder",
        "2. Configure Quality & Audio Pills",
        "3. Trigger One-Click Sync",
        "4. Live Speed & Byte Monitoring"
      ],
      "mockup_action_buttons": [
        "Start Sync",
        "Open Settings"
      ],
      "mockup_image_path": "assets/tasks.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "First-Time Walkthrough",
      "icon_name": "directions_run",
      "section_blocks": [
        {
          "heading_title": "Initial Configuration in 4 Steps",
          "block_type": "paragraph",
          "paragraph_text": "Setting up Kyaa!! takes less than two minutes. Once your library path and preferences are established, the engine operates completely autonomously—either on manual trigger or scheduled automation."
        },
        {
          "heading_title": "Step-by-Step Setup Guide",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Step 1 \u2014 Choose Library Directory:",
              "item_description": "Navigate to the Settings tab (gear icon in the navigation bar). Click the Browse button under 'Anime Target Folder' to launch the native Windows folder picker and select your root anime media folder."
            },
            {
              "highlighted_prefix": "Step 2 \u2014 Set Quality & Audio Preferences:",
              "item_description": "In Settings Section 2, select your preferred resolution (1080p Full HD or 720p HD) and audio format (Subtitled Japanese or English Dubbed). Preferences persist across app sessions."
            },
            {
              "highlighted_prefix": "Step 3 \u2014 SafetyGuard Baseline Scan:",
              "item_description": "Upon selecting your directory, SafetyGuard takes a sub-millisecond atomic snapshot of existing files to guarantee zero overwrite or deletion risks."
            },
            {
              "highlighted_prefix": "Step 4 \u2014 Run Synchronization:",
              "item_description": "Click the prominent 'Run Sync' button located on the titlebar or the Tasks page. Kyaa!! will launch the Python background engine, scan your folders, match missing episodes on mirrors, and stream transfers."
            }
          ]
        },
        {
          "heading_title": "Settings Configuration View",
          "block_type": "image",
          "image_path": "assets/settings.png",
          "alt_text": "Settings view showing folder path picker, quality selector, and ignored anime chip list",
          "caption_text": "Figure 2: The Settings View provides intuitive control over library paths, resolution, audio streams, and exclusions."
        },
        {
          "heading_title": "Monitoring Live Synchronizations",
          "block_type": "paragraph",
          "paragraph_text": "During synchronization, the Tasks tab displays all ongoing operations. You can see real-time download speeds in MB/s, transferred byte counts, dynamic progress bars, and status pills (Queued, In Progress, Completed, Failed). If any mirror error occurs, clicking the error pill opens the error details modal."
        }
      ]
    },
    {
      "tab_title": "Best Practices",
      "icon_name": "tips_and_updates",
      "section_blocks": [
        {
          "heading_title": "Recommended Folder & Filename Conventions",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! supports standard folder layouts used by media servers like Plex, Jellyfin, and Kodi. The hybrid regex and AI parsing engine tolerates diverse naming styles, but adhering to clean conventions ensures the fastest matching."
        },
        {
          "heading_title": "Library Layout Compatibility",
          "block_type": "table",
          "table_headers": [
            "Folder Hierarchy",
            "Example File Format",
            "Parser Recognition"
          ],
          "table_rows": [
            [
              "Root / Show Name / Season / File",
              "D:/Anime/Frieren/Season 1/Frieren 01.mp4",
              "Optimal (Direct regex match)"
            ],
            [
              "Root / Show Name / File",
              "D:/Anime/Solo Leveling/Solo Leveling - E12.mkv",
              "Optimal (Standard pattern)"
            ],
            [
              "Release Group Release Tags",
              "D:/Anime/[SubsPlease] Dandadan - 05 (1080p).mkv",
              "Auto-Stripped (Hashtag/bracket filter)"
            ],
            [
              "Complex Season Subtitles",
              "D:/Anime/Re Zero S2 Part 2/ReZero 24.mp4",
              "AI Multi-token parsing enabled"
            ]
          ]
        },
        {
          "heading_title": "Usage Tips & Troubleshooting",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Avoid File Locks During Sync:",
              "item_description": "Ensure media players (e.g., VLC, MPC-HC) are not locking partially downloaded .mp4.part files while synchronization is active."
            },
            {
              "highlighted_prefix": "Ignoring Completed Shows:",
              "item_description": "Add completed or archived anime series to the 'Ignored Anime' chip list in Settings to skip unnecessary mirror catalog scans."
            },
            {
              "highlighted_prefix": "Automatic Error Resumption:",
              "item_description": "If your internet connection drops, the Circuit Breaker will pause and resume download chunks automatically without corrupting partially downloaded episodes."
            }
          ]
        }
      ]
    }
  ]
};
