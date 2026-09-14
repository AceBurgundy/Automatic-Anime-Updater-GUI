# Anime Refresher

Automated anime episode tracking and video downloader for local unwatched collections and the Animepahe mirror network. Features Camoufox stealth browser automation with Cloudflare Turnstile bypass, audio preference routing, in-process AI model integration, and real-time JSON streaming for external frontends (such as Flutter and Electron).

---

## Key Features

- **Stealth Automation**: Built with Camoufox anti-detect browser engine for automated Cloudflare Turnstile bypass, JS evaluation, and Kwik direct CDN token decryption.
- **Audio Preference Prioritization**: Supports Subbed vs. Dubbed stream routing (`sub`, `dub`, `sub_strict`, `dub_strict`) across 1080p and 720p resolutions with retry tracking.
- **In-Process AI Model Engine**: Self-contained local GGUF model manager (`Qwen 2.5 0.5B`) for intelligent episode number extraction and naming pattern matching with zero external dependencies.
- **Real-Time Subprocess Streaming (`--start-automation-stream`)**: Emits single-line type-prepended JSON events on `stdout` with live percentage, byte counters, download status, and error logs for Flutter / UI integrations.
- **Safety Snapshot Protection**: Arming pre-run snapshot validation guaranteeing zero write, delete, edit, or rename access to pre-existing collection files.
- **Centralized Constants (`constants.py`)**: Isolates all model URLs, filenames, selectors, and defaults in a single configuration file for easy future upgrades.

---

## Installation & Setup

1. **Clone the Repository**:
   ```cmd
   git clone <repo-url>
   cd anime-refresher
   ```

2. **Initialize Python Virtual Environment**:
   ```cmd
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   .venv\Scripts\playwright install chromium
   ```

3. **Download the Embedded AI Model**:
   ```cmd
   .venv\Scripts\python.exe main.py --download-model
   ```

---

## CLI Command Reference

Running `python main.py` with **no arguments** displays the active settings and full guide menu automatically.

### 1. Automation & Execution
| Parameter | Description & Instructions | Example |
| :--- | :--- | :--- |
| `(no arguments)` | Displays active settings and full command reference menu | `python main.py` |
| `--start-automation` | Scrapes Animepahe and downloads missing anime episodes | `python main.py --start-automation` |
| `--start-automation-stream` | Runs automation while emitting real-time JSON stream on `stdout` | `python main.py --start-automation-stream` |
| `--dry-run` | Simulates execution without writing or downloading files | `python main.py --start-automation --dry-run` |
| `--single-cycle` | Runs a single check/download pass and exits immediately | `python main.py --start-automation --single-cycle` |
| `--maximum-downloads <N>` | Caps the number of episode downloads in a single session | `python main.py --start-automation --maximum-downloads 3` |
| `--headful-browser` | Launches browser in visible GUI mode for debugging | `python main.py --start-automation --headful-browser` |
| `--verbose` | Enables comprehensive `DEBUG` level logging | `python main.py --start-automation --verbose` |

### 2. Configuration & Settings
| Parameter | Description & Instructions | Example |
| :--- | :--- | :--- |
| `--set-target-directory "<PATH>"` | Updates anime storage directory in `.env` | `python main.py --set-target-directory "D:\Videos\Anime Unwatched"` |
| `--set-audio-preference <PREF>` | Sets audio preference (`sub`, `dub`, `sub_strict`, `dub_strict`) | `python main.py --set-audio-preference dub` |
| `--set-preferred-resolution <RES>` | Sets default download resolution (`1080`, `720`, `480`, `360`) | `python main.py --set-preferred-resolution 720` |
| `--set-folder-as-title` | Enables strict folder-based naming | `python main.py --set-folder-as-title` |
| `--unset-folder-as-title` | Disables strict folder-based naming | `python main.py --unset-folder-as-title` |
| `--ignore <ITEMS...>` | Adds folders or files to persistent ignore list | `python main.py --ignore Others` |
| `--list-ignored` | Displays all currently ignored items | `python main.py --list-ignored` |
| `--unignore <ITEMS...>` | Removes items from ignore list | `python main.py --unignore Others` |
| `--reset-ignored` | Clears all items from ignore list | `python main.py --reset-ignored` |
| `--set-model-url "<URL>"` | Updates GGUF model download URL in `.env` | `python main.py --set-model-url "https://huggingface.co/..."` |
| `--download-model` | Downloads and verifies the AI model file in `models/` | `python main.py --download-model` |
| `--setup-task-scheduler` | Registers automated Windows Task Scheduler triggers | `python main.py --setup-task-scheduler` |
| `--remove-task-scheduler` | Removes automated Windows Task Scheduler triggers | `python main.py --remove-task-scheduler` |

---

## Subprocess Streaming Integration (Flutter / Dart Example)

When using `--start-automation-stream`, standard output emits single-line JSON event objects:

```dart
import 'dart:convert';
import 'dart:io';

Future<void> listenToAnimeRefresher() async {
  var process = await Process.start('python', ['main.py', '--start-automation-stream']);

  process.stdout
      .transform(utf8.decoder)
      .transform(const LineSplitter())
      .listen((line) {
    if (line.trim().startsWith('{')) {
      var event = jsonDecode(line);
      String status = event['string_download_status'];
      String anime = event['string_anime_name'];
      double progress = (event['float_progress_percentage'] as num).toDouble();

      print('[$status] $anime: $progress%');

      if (status == 'failed') {
        print('Error Summary: ${event['string_short_error_message']}');
        print('Full Traceback: ${event['string_error_log_message']}');
      }
    }
  });
}
```

---

## Automated Scheduled Tasks

To register daily background runs (default: `06:00`, `12:00`, `22:00`):
```cmd
python main.py --setup-task-scheduler
```
To trigger on-demand automation:
```cmd
C:\shortcuts\anime-refresher.bat
```
