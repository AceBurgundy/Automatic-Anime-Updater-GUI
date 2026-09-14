/**
 * Navigation item specification: Installation & Setup.
 */
window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};
window.DOCUMENTATION_ITEMS["data/navigation-items/installation-and-setup.js"] = {
  "item_title": "Installation & Setup",
  "icon_name": "download",
  "header_container": {
    "title": "Installation & Setup Guide",
    "description": "Install Kyaa!! Anime Refresher using the standalone Windows Setup Wizard, run portably without installation, or configure a local development environment from source.",
    "badge_list": [
      { "icon_name": "inventory_2",     "badge_label": "Standalone Setup Wizard" },
      { "icon_name": "desktop_windows", "badge_label": "Windows 10/11 x64" },
      { "icon_name": "bolt",            "badge_label": "Portable Zero-Install Mode" },
      { "icon_name": "code",            "badge_label": "Source Build (Flutter & Python)" }
    ],
    "mockup_card": {
      "mockup_title": "Installation Options",
      "mockup_options": [
        "1. GUI Setup Wizard (Setup.bat / Install-Kyaa.ps1)",
        "2. Portable Execution (app/kyaa.exe)",
        "3. GitHub Releases Distribution",
        "4. Developer Source Clone"
      ],
      "mockup_action_buttons": [
        "Download Release",
        "View Source"
      ],
      "mockup_image_path": "assets/settings.png"
    }
  },
  "tab_list": [
    {
      "tab_title": "User Installation",
      "icon_name": "desktop_windows",
      "section_blocks": [
        {
          "heading_title": "Installing via GitHub Releases Package",
          "block_type": "paragraph",
          "paragraph_text": "Kyaa!! Anime Refresher is distributed as a self-contained Windows release package. It includes all pre-compiled Flutter desktop runner binaries, the Python runtime environment, Camoufox stealth browser dependencies, and an interactive dark-themed GUI installer wizard."
        },
        {
          "heading_title": "Installation Steps",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "1. Download Release Package:",
              "item_description": "Visit the GitHub Releases page and download the latest KyaaApp_v1.0.0_Windows_Setup.zip archive."
            },
            {
              "highlighted_prefix": "2. Extract the Archive:",
              "item_description": "Unpack the downloaded zip file into any directory using Windows Explorer, 7-Zip, or WinRAR."
            },
            {
              "highlighted_prefix": "3. Run Setup.bat:",
              "item_description": "Double-click Setup.bat. This launches the Kyaa!! Setup Wizard with AMOLED Dark styling."
            },
            {
              "highlighted_prefix": "4. Complete Wizard:",
              "item_description": "Select your installation directory (defaults to %LOCALAPPDATA%\\Programs\\KyaaApp), toggle Desktop and Start Menu shortcuts, and click Install. The wizard stages the application and creates your shortcuts."
            }
          ]
        },
        {
          "heading_title": "Portable Execution (Zero Install)",
          "block_type": "paragraph",
          "paragraph_text": "If you prefer not to install Kyaa!! into your system programs folder, you can run it completely portably. Simply extract the zip file, navigate into the app folder, and launch kyaa.exe directly. All state and settings remain contained."
        },
        {
          "heading_title": "System Requirements",
          "block_type": "table",
          "table_headers": [
            "Component",
            "Minimum Requirement",
            "Recommended Specification"
          ],
          "table_rows": [
            [
              "Operating System",
              "Windows 10 64-bit (Build 19041+)",
              "Windows 11 64-bit (22H2+)"
            ],
            [
              "Python Runtime",
              "Bundled in Release Package",
              "Bundled in Release Package"
            ],
            [
              "System Memory (RAM)",
              "4 GB Physical RAM",
              "8 GB+ (for local AI episode model)"
            ],
            [
              "Storage Space",
              "800 MB Free Space",
              "2.0 GB Free Space (with Qwen2.5 GGUF)"
            ],
            [
              "Display Resolution",
              "1280 x 720 minimum",
              "1920 x 1080 Full HD (60fps AMOLED UI)"
            ]
          ]
        }
      ]
    },
    {
      "tab_title": "Developer Setup",
      "icon_name": "terminal",
      "section_blocks": [
        {
          "heading_title": "Building and Running From Source",
          "block_type": "paragraph",
          "paragraph_text": "If you wish to contribute to Kyaa!! or inspect the codebase, clone the repository and run both the Flutter frontend and Python backend in developer mode."
        },
        {
          "heading_title": "Repository Clone & Environment Provisioning",
          "block_type": "code_block",
          "header_label": "PowerShell \u2022 Workspace Root",
          "language_identifier": "powershell",
          "code_content": "# 1. Clone repository\ngit clone https://github.com/AceBurgundy/kyaa_anime_refresher.git\ncd kyaa_anime_refresher\n\n# 2. Set up Python backend virtual environment\ncd backend\npython -m venv env\n.\\env\\Scripts\\activate\npip install -r requirements.txt\ncamoufox fetch\ncd ..\n\n# 3. Restore Flutter dependencies and launch\nflutter pub get\nflutter run -d windows"
        },
        {
          "heading_title": "Optional AI Model Download",
          "block_type": "paragraph",
          "paragraph_text": "For intelligent episode title and token parsing, download the quantized Qwen2.5-0.5B-Instruct GGUF model weights (~398MB) directly through the CLI or via the Settings tab inside the app."
        },
        {
          "heading_title": "CLI Model Download Command",
          "block_type": "code_block",
          "header_label": "PowerShell \u2022 backend directory",
          "language_identifier": "powershell",
          "code_content": ".\\env\\Scripts\\python.exe main.py --download-model"
        },
        {
          "heading_title": "Packaging Custom Installers",
          "block_type": "diamond_list",
          "diamond_items": [
            {
              "highlighted_prefix": "build_installer.ps1:",
              "item_description": "Run packaging/build_installer.ps1 in PowerShell to compile the Flutter Windows release, bundle the backend virtual environment, and generate KyaaApp_v1.0.0_Windows_Setup.zip in dist/."
            },
            {
              "highlighted_prefix": "Inno Setup Compiler:",
              "item_description": "Compile packaging/kyaa_installer.iss using Inno Setup 6 to generate a standalone signed setup executable (KyaaSetup.exe)."
            }
          ]
        }
      ]
    }
  ]
};
