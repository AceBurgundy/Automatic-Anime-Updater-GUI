/**
 * Navigation item specification: Dashboard Landing Page for Kyaa!! Anime Refresher.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/dashboard.js"] = {
  "item_title": "Dashboard",
  "icon_name": "dashboard",
  "header_container": {
    "title": "Kyaa!! Anime Refresher",
    "description": "The ultimate automated anime episode synchronization engine and anti-detect downloader, featuring an AMOLED Dark Flutter desktop companion, real-time NDJSON event streaming, Camoufox stealth browser automation, and multi-tier mirror failover resilience.",
    "badge_list": [
      { "icon_name": "desktop_windows", "badge_label": "Flutter 3.22+ Desktop" },
      { "icon_name": "security",        "badge_label": "Camoufox Anti-Detect" },
      { "icon_name": "terminal",        "badge_label": "Python 3.10+ Backend" },
      { "icon_name": "psychology",      "badge_label": "Qwen2.5 AI Parser" },
      { "icon_name": "bolt",            "badge_label": "Fast Mirror Failover" },
      { "icon_name": "verified",        "badge_label": "Version 1.1.0" }
    ],
    "banner_image": { "image_path": "assets/tasks.png", "shrink": false },
    "mockup_card":  { "image_path": "assets/tasks.png", "shrink": false }
  },
  "tab_list": [
    {
      "tab_title": "Dashboard",
      "icon_name": "dashboard",
      "section_blocks": [
        {
          "heading_title": "Core Application Views & Experience",
          "block_type": "cards_container",
          "description": "Navigate through the primary desktop modules built to provide zero-friction anime library management, instant status updates, and automated background syncing.",
          "layout_type": "three_cards",
          "cards": [
            {
              "title": "Tasks & Real-Time Streaming",
              "description": "Live NDJSON stream dashboard displaying real-time download percentages, transfer speeds in MB/s, transferred byte counts, and full failure logs.",
              "label": "Live Stream View",
              "link": "data/navigation-items/tasks-and-live-streaming.js"
            },
            {
              "title": "Library & Quality Settings",
              "description": "Configure your local unwatched anime storage directory, AI model installation, audio track preferences (Sub/Dub), resolution rules, and dynamic ignore lists.",
              "label": "Settings View",
              "link": "data/navigation-items/library-and-settings.js"
            },
            {
              "title": "Scheduling & Automation Triggers",
              "description": "Set automated recurring triggers using an intuitive 12-hour time picker and weekday selection, backed by native Windows Task Scheduler triggers.",
              "label": "Automation View",
              "link": "data/navigation-items/scheduling-and-automation.js"
            }
          ]
        },
        {
          "heading_title": "Engineering & Resilience Architecture",
          "block_type": "cards_container",
          "description": "Engineered with anti-detect browser stealth, automated circuit breaker recovery, and intelligent heuristic filename extraction.",
          "layout_type": "five_cards",
          "cards": [
            {
              "title": "Camoufox Anti-Detect Engine",
              "description": "Passes Cloudflare Turnstile behavioral checks using realistic humanized cursor trajectories and stealth fingerprint injection.",
              "label": "Stealth Engine",
              "link": "data/navigation-items/anti-detect-and-camoufox.js"
            },
            {
              "title": "Circuit Breaker & Mirror Failover",
              "description": "Automatic 30s cooldown and session reset upon consecutive challenge errors, cycling dynamically across .pw, .org, .com, and .ru mirrors.",
              "label": "Failover System",
              "link": "data/navigation-items/circuit-breaker-and-mirrors.js"
            },
            {
              "title": "Qwen2.5 AI Episode Parser",
              "description": "Lightweight 0.5B quantized GGUF model with fast-path regex fallback for 100% accurate episode and season number detection.",
              "label": "AI Parser",
              "link": "data/navigation-items/ai-episode-parser-model.js"
            },
            {
              "title": "Atomic SQLite3 Persistence",
              "description": "Instant <0.001s transactional migration and storage for series index cache, episode states, and dynamic ignore rules.",
              "label": "Database Engine",
              "link": "data/navigation-items/database-and-safetyguard.js"
            },
            {
              "title": "CLI Commands & Headless Ops",
              "description": "Complete command-line interface specification for headless servers, scripts, scheduled cron jobs, and background workers.",
              "label": "CLI Reference",
              "link": "data/navigation-items/cli-commands-reference.js"
            }
          ]
        },
        {
          "heading_title": "Get Started in Minutes",
          "block_type": "cards_container",
          "description": "Set up Kyaa!! Anime Refresher on Windows using the GUI setup wizard, portable release packages, or source code.",
          "layout_type": "three_cards",
          "cards": [
            {
              "title": "Overview & Architecture",
              "description": "High-level overview of the dual-process architecture, IPC bridge, and core synchronization pipeline.",
              "label": "System Overview",
              "link": "data/navigation-items/overview-and-architecture.js"
            },
            {
              "title": "Installation & Setup Guide",
              "description": "Standalone Windows installer wizard, portable release package, system requirements, and developer source build setup.",
              "label": "Setup Guide",
              "link": "data/navigation-items/installation-and-setup.js"
            },
            {
              "title": "Quickstart & First Run",
              "description": "Step-by-step walkthrough for configuring your anime folder, running your first library sync, and inspecting downloaded episodes.",
              "label": "Quickstart",
              "link": "data/navigation-items/quickstart-and-usage.js"
            }
          ]
        }
      ]
    }
  ]
};
