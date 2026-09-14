/**
 * Navigation item specification: Theming & Design System.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/theming-and-design-system.js"] = {
  "item_title": "Theming & Design System",
  "icon_name": "palette",
  "header_container": {
    "title": "Theming & Design System",
    "description": "A modern frameless AMOLED Dark design system built on Material Design 3, custom Win32 titlebars, Google Sans typography, and dynamic accent color palettes.",
    "badge_list": [
      { "icon_name": "dark_mode",     "badge_label": "AMOLED True Dark" },
      { "icon_name": "crop_portrait", "badge_label": "Frameless Win32 Window" },
      { "icon_name": "font_download", "badge_label": "Google Sans Typography" },
      { "icon_name": "color_lens",    "badge_label": "Dynamic Accent Palettes" }
    ],
    "mockup_card": {
      "mockup_title": "Theme Customizer",
      "mockup_options": [
        "1. AMOLED True Dark (#0F0F13)",
        "2. Crimson Kyaa Red (#FF3366)",
        "3. Cyber Cyan (#00E5FF)",
        "4. Sakura Blossom Pink (#FF69B4)",
        "5. Electric Purple (#BB86FC)"
      ],
      "mockup_action_buttons": [
        "Apply Theme",
        "Preview Palette"
      ],
      "mockup_image_path": "assets/themes.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "Design Philosophy",
      "icon_name": "brush",
      "section_blocks": [
        {
          "heading_title": "Modern Frameless AMOLED Aesthetic",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! Anime Refresher rejects clunky, standard OS window borders in favor of a sleek, bespoke desktop experience. Built using bitsdojo_window and Flutter's rendering pipeline, it delivers true 60fps frameless window movement, deep AMOLED blacks, and high-contrast typography."
        },
        {
          "heading_title": "Theme Customization Viewport",
          "block_type": "image",
          "image_path": "assets/themes.png",
          "alt_text": "Themes view showing AMOLED dark cards and accent color palettes",
          "caption_text": "Figure 6: The Themes View allows switching between vibrant accent colorways on deep AMOLED obsidian surfaces."
        },
        {
          "heading_title": "Visual & Interaction Pillars",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "Frameless Win32 Windowing:",
              "item_description": "Integrated custom titlebar with drag regions, maximize/restore, minimize, and close buttons that blend seamlessly with the app's dark header."
            },
            {
              "highlighted_prefix": "AMOLED Obsidian Contrast:",
              "item_description": "Background tones are anchored at #0F0F13 and cards at #1A1A24 to minimize eye strain and save power on modern OLED/Mini-LED displays."
            },
            {
              "highlighted_prefix": "Google Sans Typography:",
              "item_description": "Typography is strictly structured around Google Sans and JetBrains Mono for code/logs, providing crisp legibility across high-DPI monitors."
            },
            {
              "highlighted_prefix": "Subtle Depth & Outlines:",
              "item_description": "Instead of heavy drop shadows, Kyaa!! utilizes delicate 1px borders (#2D2D3D) and gentle border radii (12px) to define structural hierarchy."
            }
          ]
        }
      ]
    },
    {
      "tab_title": "Design Tokens & Palettes",
      "icon_name": "style",
      "section_blocks": [
        {
          "heading_title": "Color Token Specification",
          "block_type": "paragraph",
          "paragraph_text": "The theme engine defines strict semantic tokens for backgrounds, surfaces, text hierarchies, and accent indicators. All widgets consume these tokens rather than hardcoded hex values."
        },
        {
          "heading_title": "Core Palette Design Tokens",
          "block_type": "table",
          "table_headers": [
            "Token Name",
            "Color Value",
            "Usage Context"
          ],
          "table_rows": [
            [
              "kBackgroundDark",
              "#0F0F13",
              "Primary window and scaffolding background"
            ],
            [
              "kSurfaceElevated",
              "#1A1A24",
              "Task cards, settings panels, and navigation containers"
            ],
            [
              "kBorderSubtle",
              "#2D2D3D",
              "1px card dividers and container outlines"
            ],
            [
              "kAccentCrimson",
              "#FF3366",
              "Default Kyaa primary action color and active pills"
            ],
            [
              "kAccentCyan",
              "#00E5FF",
              "Active download progress bars and live speed counters"
            ],
            [
              "kTextPrimary",
              "#FFFFFF",
              "Headings, card titles, and active labels"
            ],
            [
              "kTextSecondary",
              "#9E9EA8",
              "Descriptions, muted metadata, and subtitle labels"
            ]
          ]
        },
        {
          "heading_title": "Dart ThemeData Implementation",
          "block_type": "code_block",
          "header_label": "Dart \u2022 theme_constants.dart",
          "language_identifier": "dart",
          "code_content": "final darkTheme = ThemeData(\n  brightness: Brightness.dark,\n  scaffoldBackgroundColor: const Color(0xFF0F0F13),\n  cardColor: const Color(0xFF1A1A24),\n  colorScheme: const ColorScheme.dark(\n    primary: Color(0xFFFF3366),\n    secondary: Color(0xFF00E5FF),\n    surface: Color(0xFF1A1A24),\n    background: Color(0xFF0F0F13),\n  ),\n  fontFamily: 'GoogleSans',\n  dividerColor: const Color(0xFF2D2D3D),\n);"
        }
      ]
    }
  ]
};
