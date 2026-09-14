/**
 * Navigation item specification: Circuit Breaker & Mirrors.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/circuit-breaker-and-mirrors.js"] = {
  "item_title": "Circuit Breaker & Mirrors",
  "icon_name": "electrical_services",
  "header_container": {
    "title": "Autonomous Circuit Breaker & Mirror Rotation",
    "description": "High-availability scraping resilience with consecutive failure triggers, cooldown backoff cycles, dynamic mirror failover (.pw \u2192 .org \u2192 .com \u2192 .ru), and automated HTML error dashboards.",
    "badge_list": [
      { "icon_name": "warning",    "badge_label": "Consecutive Failure Trip" },
      { "icon_name": "timer",      "badge_label": "Cooldown Backoff (30s)" },
      { "icon_name": "swap_calls", "badge_label": "Dynamic Mirror Failover" },
      { "icon_name": "html",       "badge_label": "errors.html Dashboard" }
    ],
    "mockup_card": {
      "mockup_title": "Resilience Controller",
      "mockup_options": [
        "1. State: HEALTHY (Zero consecutive errors)",
        "2. Trip Threshold: >= 2 Consecutive Failures",
        "3. Mirror Failover: .pw \u2192 .org \u2192 .com \u2192 .ru",
        "4. Auto-Generated: errors.html Diagnostic"
      ],
      "mockup_action_buttons": [
        "Reset Breaker",
        "Open Error Report"
      ],
      "mockup_image_path": "assets/tasks.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Circuit Breaker Pattern",
      "icon_name": "power_settings_new",
      "section_blocks": [
        {
          "heading_title": "Self-Healing Scraper Architecture",
          "block_type": "paragraph",
          "paragraph_text": "Scraping media mirrors is inherently volatile: mirror domains get seized, Cloudflare challenges escalate, or server CDNs encounter 503 gateway timeouts. Rather than crashing or hammering servers until your IP is blacklisted, Kyaa!! employs an autonomous, self-healing Circuit Breaker pattern."
        },
        {
          "heading_title": "The Three Circuit States",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "CLOSED (Normal Operation):",
              "item_description": "Requests proceed normally. Successful episode resolutions continuously reset the consecutive failure counter to zero."
            },
            {
              "highlighted_prefix": "OPEN (Tripped):",
              "item_description": "Triggered when \u2265 2 consecutive anime fail. All scraping halts immediately. The engine purges browser sessions, enters a 30-second cooldown backoff, and switches to the next mirror domain in the priority list."
            },
            {
              "highlighted_prefix": "HALF-OPEN (Canary Trial):",
              "item_description": "After the cooldown elapses, the engine tests a single episode resolution on the new mirror. If successful, the circuit resets to CLOSED; if it fails, it trips back to OPEN with doubled backoff."
            }
          ]
        },
        {
          "heading_title": "Dynamic Mirror Rotation Chain",
          "block_type": "table",
          "table_headers": [
            "Priority",
            "Mirror Domain",
            "Region / Infrastructure",
            "Failover Criteria"
          ],
          "table_rows": [
            [
              "1 (Primary)",
              "animepahe.pw",
              "Global Cloudflare Edge",
              "Default initial connection"
            ],
            [
              "2 (Fallback A)",
              "animepahe.org",
              "Secondary Edge Network",
              "Tripped on 2x consecutive failures"
            ],
            [
              "3 (Fallback B)",
              "animepahe.com",
              "Alternative routing",
              "Tripped if Fallback A is unreachable"
            ],
            [
              "4 (Fallback C)",
              "animepahe.ru",
              "Eastern European Mirror",
              "Final fallback endpoint"
            ]
          ]
        },
        {
          "heading_title": "Circuit Breaker Python Implementation",
          "block_type": "code_block",
          "header_label": "Python \u2022 scraper/circuit_breaker.py",
          "language_identifier": "python",
          "code_content": "class CircuitBreaker:\n    def __init__(self, threshold: int = 2, cooldown_sec: float = 30.0):\n        self.threshold = threshold\n        self.cooldown_sec = cooldown_sec\n        self.failure_count = 0\n        self.state = \"CLOSED\"\n        self.last_failure_time = 0.0\n\n    def record_failure(self):\n        self.failure_count += 1\n        if self.failure_count >= self.threshold:\n            self.state = \"OPEN\"\n            self.last_failure_time = time.time()\n            rotate_mirror_domain()\n\n    def record_success(self):\n        self.failure_count = 0\n        self.state = \"CLOSED\""
        }
      ]
    },
    {
      "tab_title": "Telemetry & Error Reports",
      "icon_name": "history_edu",
      "section_blocks": [
        {
          "heading_title": "Automated HTML Error Dashboard (errors.html)",
          "block_type": "paragraph",
          "paragraph_text": "Whenever an unrecoverable failure or circuit trip occurs, Kyaa!! automatically synthesizes an interactive diagnostic report saved to errors.html in your application directory. The report includes exact HTTP status codes, browser console logs, mirror response snapshots, and timestamped error stack traces."
        },
        {
          "heading_title": "Error Taxonomy & Auto-Remediation",
          "block_type": "table",
          "table_headers": [
            "Error Condition",
            "HTTP / Engine Code",
            "Root Cause",
            "Automated Remedy"
          ],
          "table_rows": [
            [
              "Turnstile Lock",
              "HTTP 403",
              "Cloudflare challenge did not pass in time",
              "Re-initializes Camoufox with refreshed WebGL fingerprint"
            ],
            [
              "Rate Throttling",
              "HTTP 429",
              "Mirror API requested too rapidly",
              "Trips circuit breaker; enforces 30s exponential backoff"
            ],
            [
              "Bad Gateway",
              "HTTP 502 / 503",
              "Mirror server is temporarily offline",
              "Rotates instantly to next mirror (.pw \u2192 .org \u2192 .com)"
            ],
            [
              "Episode Missing",
              "HTTP 404",
              "Show has not been uploaded to mirror yet",
              "Logs non-fatal warning; continues remaining show queue"
            ]
          ]
        },
        {
          "heading_title": "Diagnostic Workflow for Users",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "In-App Error Inspection:",
              "item_description": "Click the red 'Failed' status badge on any task card in the Tasks tab to view the immediate error summary."
            },
            {
              "highlighted_prefix": "Full HTML Visualizer:",
              "item_description": "Open errors.html in Chrome, Edge, or Firefox to view rendered DOM screenshots taken by Camoufox at the moment of failure."
            },
            {
              "highlighted_prefix": "Zero-Loss Resumption:",
              "item_description": "Once mirrors stabilize, running 'Run Sync' picks up exactly where the process left off without re-downloading finished episodes."
            }
          ]
        }
      ]
    }
  ]
};
