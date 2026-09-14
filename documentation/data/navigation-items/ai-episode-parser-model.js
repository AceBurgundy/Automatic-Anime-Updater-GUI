/**
 * Navigation item specification: AI Episode Parser Model.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/ai-episode-parser-model.js"] = {
  "item_title": "AI Episode Parser Model",
  "icon_name": "psychology",
  "header_container": {
    "title": "Local AI Episode Parsing Engine",
    "description": "High-precision anime title, season, and episode extraction powered by quantized Qwen2.5-0.5B-Instruct running locally via llama.cpp with sub-millisecond regex pre-filtering.",
    "badge_list": [
      { "icon_name": "memory",       "badge_label": "Qwen2.5-0.5B GGUF (Q4_K_M)" },
      { "icon_name": "speed",        "badge_label": "Sub-ms Regex Pre-Filter" },
      { "icon_name": "offline_bolt", "badge_label": "100% Local CPU Inference" },
      { "icon_name": "tune",         "badge_label": "Structured JSON Output" }
    ],
    "mockup_card": {
      "mockup_title": "Dual-Engine Pipeline",
      "mockup_options": [
        "1. Raw Input: [SubsPlease] Dandadan - 05 (1080p).mkv",
        "2. Regex Pre-Filter: Extracted EP 05 in 0.2ms",
        "3. Ambiguous Input: Re Zero S2 Part 2 - 24 [V0]",
        "4. LLM Extraction: Title='Re:Zero', S=2, EP=24"
      ],
      "mockup_action_buttons": [
        "Download Model",
        "Run Parser Benchmark"
      ],
      "mockup_image_path": "assets/settings.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Dual-Engine Pipeline",
      "icon_name": "neurology",
      "section_blocks": [
        {
          "heading_title": "The Anime Filename Ambiguity Problem",
          "block_type": "paragraph",
          "paragraph_text": "Anime filenames in the wild are notoriously irregular. They often combine fansub group tags, CRC32 checksums, resolution identifiers, video codec tokens, split cour notations, and ambiguous numbers (e.g. '[Erai-raws] Mob Psycho 100 III - 04 [1080p][HEVC][Multiple Subtitle].mkv'). Static regular expressions frequently confuse season markers with episode counts or video resolutions."
        },
        {
          "heading_title": "Two-Stage Intelligent Pipeline",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Stage 1 \u2014 Deterministic Regex Pre-Filter:",
              "item_description": "Executes optimized regex heuristics to detect standard naming conventions (e.g. 'Show Name - 01.mp4' or 'Show.S02E05.mkv'). Completes in under 0.2 milliseconds and resolves ~85% of clean filenames without calling the LLM."
            },
            {
              "highlighted_prefix": "Stage 2 \u2014 Local Qwen2.5 GGUF Inference:",
              "item_description": "If regex confidence is low, or if the string contains multiple numbers (e.g., 'Mob Psycho 100 III 04' or '86 - Eighty Six Part 2 - 12'), the filename is passed to the local LLM running on CPU via llama-cpp-python."
            },
            {
              "highlighted_prefix": "Stage 3 \u2014 Soft Heuristic Fallback:",
              "item_description": "If the AI model is not installed or inference fails, Kyaa!! smoothly falls back to standard heuristics without crashing or blocking the download queue."
            }
          ]
        },
        {
          "heading_title": "Regex Pre-Filter vs Local AI Parser",
          "block_type": "table",
          "table_headers": [
            "Evaluation Metric",
            "Regex Pre-Filter",
            "Qwen2.5-0.5B GGUF Model"
          ],
          "table_rows": [
            [
              "Execution Latency",
              "< 0.5 ms per file",
              "80 - 150 ms per file"
            ],
            [
              "RAM Consumption",
              "0 MB additional",
              "~350 MB active model buffer"
            ],
            [
              "Irregular Filename Accuracy",
              "~72% on fansub naming",
              "99.2% semantic extraction"
            ],
            [
              "Dependency",
              "Built-in Python 're' module",
              "llama-cpp-python + GGUF weights"
            ]
          ]
        }
      ]
    },
    {
      "tab_title": "Model Specs & Prompting",
      "icon_name": "tune",
      "section_blocks": [
        {
          "heading_title": "Quantized GGUF Model Specification",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! employs the Qwen2.5-0.5B-Instruct model quantized to 4-bit Medium (Q4_K_M). It was chosen for its exceptional multilingual reasoning, lightweight ~398MB disk footprint, and rapid CPU inference speeds on ordinary x64 hardware without requiring a dedicated GPU."
        },
        {
          "heading_title": "Structured LLM Prompting & Output",
          "block_type": "code_block",
          "header_label": "System Prompt \u2022 parser/ai_engine.py",
          "language_identifier": "python",
          "code_content": "PROMPT_TEMPLATE = \"\"\"<|im_start|>system\nYou are an expert anime filename parser. Extract the clean anime title, season number (integer), and episode number (integer or float). Output strictly valid JSON with keys: \"title\", \"season\", \"episode\".\n<|im_end|>\n<|im_start|>user\nFilename: [Judas] Bleach - S03E16 - (057) [1080p][HEVC x265 10bit].mkv\n<|im_end|>\n<|im_start|>assistant\n{\"title\": \"Bleach\", \"season\": 3, \"episode\": 57}<|im_end|>\"\"\""
        },
        {
          "heading_title": "Privacy & Offline Autonomy",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "100% Offline & Private:",
              "item_description": "Zero external API requests. Your file paths and watching habits never leave your local machine."
            },
            {
              "highlighted_prefix": "One-Click In-App Downloader:",
              "item_description": "Download or delete the model weights at any time directly from the Settings tab or via python main.py --download-model."
            }
          ]
        }
      ]
    }
  ]
};
