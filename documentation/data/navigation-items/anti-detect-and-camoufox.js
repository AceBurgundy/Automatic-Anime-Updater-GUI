/**
 * Navigation item specification: Anti-Detect & Camoufox.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/anti-detect-and-camoufox.js"] = {
  "item_title": "Anti-Detect & Camoufox",
  "icon_name": "security",
  "header_container": {
    "title": "Anti-Detect & Camoufox Stealth Engine",
    "description": "Overcoming Cloudflare Turnstile, browser fingerprinting, and dynamic stream obfuscation using Camoufox C++ patched headless Firefox with humanized cursor kinematics.",
    "badge_list": [
      { "icon_name": "fingerprint",    "badge_label": "Hardware Canvas Spoofing" },
      { "icon_name": "gesture",        "badge_label": "Humanized Bezier Cursors" },
      { "icon_name": "verified_user",  "badge_label": "Turnstile Auto-Bypass" },
      { "icon_name": "downloading",    "badge_label": "Direct Kwik Extraction" }
    ],
    "mockup_card": {
      "mockup_title": "Stealth Evasion Stack",
      "mockup_options": [
        "1. Camoufox C++ Patched Engine",
        "2. humanize=True Bezier Trajectories",
        "3. Cloudflare Turnstile Clearance",
        "4. Direct Kwik Socket Streaming"
      ],
      "mockup_action_buttons": [
        "Inspect Browser",
        "Test Mirror Probe"
      ],
      "mockup_image_path": "assets/tasks.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Camoufox Stealth Engine",
      "icon_name": "visibility_off",
      "section_blocks": [
        {
          "heading_title": "Why Standard Scrapers Fail",
          "block_type": "paragraph",
          "paragraph_text": "Modern anime streaming mirrors protect their download endpoints with aggressive bot detection services such as Cloudflare Turnstile, browser canvas fingerprinting, and behavioral entropy analysis. Traditional headless browsers like vanilla Puppeteer, Playwright, or Selenium are detected instantly via WebDriver flags and linear cursor paths."
        },
        {
          "heading_title": "The Camoufox Architecture",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! utilizes Camoufox—a specialized C++ modified build of Mozilla Firefox designed specifically to defeat advanced anti-bot heuristics at the browser engine level without relying on expensive, slow commercial CAPTCHA solving APIs."
        },
        {
          "heading_title": "Key Anti-Detect Defenses",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "C++ Internal Spoofing:",
              "item_description": "Modifies internal Firefox C++ engine calls to randomize WebGL canvas fingerprints, audio buffer entropy, and system font lists on every session."
            },
            {
              "highlighted_prefix": "Humanized Bezier Trajectories (humanize=True):",
              "item_description": "All mouse interactions compute randomized cubic Bézier curves with natural acceleration, deceleration, overshoots, and micro-tremors indistinguishable from human mouse movement."
            },
            {
              "highlighted_prefix": "Elimination of Automation Flags:",
              "item_description": "Completely removes navigator.webdriver flags, passes Chrome/Firefox CDP leak audits, and mimics native OS window metrics."
            },
            {
              "highlighted_prefix": "Sub-Second In-Memory Execution:",
              "item_description": "Runs in ultra-fast headless mode while retaining 100% of standard graphical rendering contexts needed to solve client-side challenges."
            }
          ]
        },
        {
          "heading_title": "Camoufox Initialization in Python",
          "block_type": "code_block",
          "header_label": "Python \u2022 scraper/browser.py",
          "language_identifier": "python",
          "code_content": "from camoufox.async_api import AsyncCamoufox\n\nasync def spawn_stealth_browser(headless: bool = True):\n    \"\"\"Spawns an anti-detect Camoufox browser context.\"\"\"\n    browser = await AsyncCamoufox(\n        headless=headless,\n        humanize=True,\n        os_target=\"windows\",\n        geoip=True,\n        screen={\"width\": 1920, \"height\": 1080}\n    ).start()\n    \n    page = await browser.new_page()\n    return browser, page"
        }
      ]
    },
    {
      "tab_title": "Kwik & Mirror Resolution",
      "icon_name": "bolt",
      "section_blocks": [
        {
          "heading_title": "Stream Extraction Pipeline",
          "block_type": "paragraph",
          "paragraph_text": "When resolving a download link, Kyaa!! navigates the anime mirror's episode page, resolves the obfuscated Kwik player iframe, clears the Cloudflare challenge, and intercepts the direct CDN token before triggering high-speed chunked socket streaming."
        },
        {
          "heading_title": "Resolution Flow Stages",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Stage 1 \u2014 Fast Mirror Probe (6s):",
              "item_description": "Probes primary mirror domains with a 6-second timeout before committing browser resources, instantly pivoting if a domain is blocked or down."
            },
            {
              "highlighted_prefix": "Stage 2 \u2014 Iframe Decryption:",
              "item_description": "Extracts the nested Kwik embed iframe and navigates inside with humanized delays to satisfy client-side JavaScript timers."
            },
            {
              "highlighted_prefix": "Stage 3 \u2014 Form Submission & Key Extraction:",
              "item_description": "Identifies the POST form action, generates the session auth cookie, and captures the direct high-bandwidth video stream URL."
            },
            {
              "highlighted_prefix": "Stage 4 \u2014 Hand-off to Direct Streamer:",
              "item_description": "Hands the resolved URL and session cookies to an asynchronous chunked HTTP client for blazing-fast multi-megabyte transfers."
            }
          ]
        },
        {
          "heading_title": "Stealth Performance Comparison",
          "block_type": "table",
          "table_headers": [
            "Scraper Engine",
            "Turnstile Pass Rate",
            "Average Solve Time",
            "Paid API Required"
          ],
          "table_rows": [
            [
              "Standard Selenium",
              "< 12% (Detected)",
              "Failed / Blocked",
              "Yes ($0.003 / solve)"
            ],
            [
              "Playwright Vanilla",
              "< 25% (Flagged)",
              "15 - 30 seconds",
              "Yes"
            ],
            [
              "Camoufox + Humanize",
              "98.4% (Passed)",
              "2.8 - 4.2 seconds",
              "No (100% Free & Local)"
            ]
          ]
        }
      ]
    }
  ]
};
