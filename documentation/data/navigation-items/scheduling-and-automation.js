/**
 * Navigation item specification: Scheduling & Automation.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/scheduling-and-automation.js"] = {
  "item_title": "Scheduling & Automation",
  "icon_name": "schedule",
  "header_container": {
    "title": "Scheduling & Windows Automation",
    "description": "Configure autonomous background synchronization schedules with day-of-week selectors, 12-hour time pickers, and native Windows Task Scheduler integration.",
    "badge_list": [
      { "icon_name": "calendar_month", "badge_label": "Day-of-Week Selector" },
      { "icon_name": "alarm",          "badge_label": "12-Hour TimePicker" },
      { "icon_name": "repeat",         "badge_label": "Everyday Toggle" },
      { "icon_name": "task",           "badge_label": "Windows Task Scheduler" }
    ],
    "mockup_card": {
      "mockup_title": "Automation Engine",
      "mockup_options": [
        "Active Days: Mon, Wed, Fri, Sun",
        "Sync Time: 04:30 AM",
        "Run Silent / Headless Mode",
        "Windows Task Scheduler: Active"
      ],
      "mockup_action_buttons": [
        "Save Schedule",
        "Trigger Now"
      ],
      "mockup_image_path": "assets/scheduling.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Scheduling Controls",
      "icon_name": "event",
      "section_blocks": [
        {
          "heading_title": "Automated Anime Library Synchronization",
          "block_type": "paragraph",
          "paragraph_text": "Never wait for new episodes to download manually. The Scheduling view lets you set recurring times and days for Kyaa!! to awaken, scan mirrors, download new simulcasts, and organize them into your folders while you sleep or work."
        },
        {
          "heading_title": "Scheduling UI Layout",
          "block_type": "image",
          "image_path": "assets/scheduling.png",
          "alt_text": "Scheduling view showing day-of-week selector pills and 12-hour time picker",
          "caption_text": "Figure 5: The Scheduling View provides day selection pills, an Everyday toggle, and a time picker."
        },
        {
          "heading_title": "Interactive Scheduling Components",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Day-of-Week Selector Pills:",
              "item_description": "Toggle individual days (Mon, Tue, Wed, Thu, Fri, Sat, Sun) to match anime release schedules (e.g., weekends for shonen releases)."
            },
            {
              "highlighted_prefix": "'Everyday' Master Toggle:",
              "item_description": "Quickly enables or disables all 7 days with a single click, automatically synchronizing pill states."
            },
            {
              "highlighted_prefix": "12-Hour Interactive TimePicker:",
              "item_description": "Clean Material 3 time dialog allowing hours, minutes, and AM/PM selection with minute-precision scheduling."
            },
            {
              "highlighted_prefix": "Headless Background Execution:",
              "item_description": "When enabled, scheduled runs execute python.exe main.py --sync silently in the background without opening the Flutter window or stealing focus."
            }
          ]
        }
      ]
    },
    {
      "tab_title": "Windows Task Scheduler",
      "icon_name": "task",
      "section_blocks": [
        {
          "heading_title": "Native OS Scheduler Integration",
          "block_type": "paragraph",
          "paragraph_text": "Rather than keeping a bloated Electron or Python tray process running 24/7 consuming battery and RAM, Kyaa!! registers standard Windows Task Scheduler jobs using schtasks.exe. The operating system handles the timer natively, spawning the CLI engine only when scheduled."
        },
        {
          "heading_title": "Windows Task Registration Command",
          "block_type": "code_block",
          "header_label": "PowerShell \u2022 schtasks integration",
          "language_identifier": "powershell",
          "code_content": "# Generated automatically by Kyaa!! when saving schedule\nschtasks /Create /TN \"KyaaAnimeRefresher_DailySync\" \\\n  /TR \"\\\"%LOCALAPPDATA%\\Programs\\KyaaApp\\backend\\env\\Scripts\\python.exe\\\" \\\"%LOCALAPPDATA%\\Programs\\KyaaApp\\backend\\main.py\\\" --sync\" \\\n  /SC WEEKLY /D MON,WED,FRI,SUN /ST 04:30 /F"
        },
        {
          "heading_title": "Key Benefits of Native Scheduling",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Zero Idle Memory Footprint:",
              "item_description": "No background daemons or tray apps remain in RAM. Windows wakes the Python worker at the scheduled minute and closes it upon sync completion."
            },
            {
              "highlighted_prefix": "Resume Upon Wakeup:",
              "item_description": "If your PC was asleep at 04:30 AM, Task Scheduler can automatically run missed tasks as soon as the machine is powered on."
            },
            {
              "highlighted_prefix": "Independent History Logging:",
              "item_description": "Scheduled runs append their transfer history directly to kyaa.db, ready to be reviewed whenever you open the Flutter desktop UI."
            }
          ]
        }
      ]
    }
  ]
};
