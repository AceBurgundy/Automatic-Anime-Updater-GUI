import argparse
import os
import subprocess
import sys
from pathlib import Path

from config import (
    PROJECT_DIR,
    TARGET_DIR,
    AUDIO_PREFERENCE,
    PREFERRED_RESOLUTION,
    MODEL_PATH,
    MODEL_URL,
    SCHEDULE_TIMES,
    BASE_URLS,
    DATABASE_PATH,
    db_manager,
)
from constants import VALID_AUDIO_PREFERENCES, VALID_RESOLUTIONS
from core.model_manager import model_manager
from core.pipeline import run_pipeline

def update_env_variable(key: str, value: str) -> None:
    """Updates or appends a key-value pair in the .env configuration file."""
    env_file = PROJECT_DIR / ".env"
    lines = []
    found = False

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"#{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{key}={value}\n")

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"[OK] Configuration updated: {key} = {value}")

def show_guide_menu() -> None:
    """Displays the comprehensive interactive terminal guide and active configuration menu."""
    model_status = "[OK] Installed" if model_manager.is_model_present() else "[!] Missing (Run --download-model)"
    model_size = f"{model_manager.get_model_size_mb()} MB" if model_manager.is_model_present() else "0 MB"
    folder_as_title = db_manager.get_bool_setting("folder_as_title", default=True)
    folder_template_str = "ENABLED (<Folder Name> <01>.<ext>)" if folder_as_title else "DISABLED (Sequential / AI)"
    ignored_count = len(db_manager.get_ignored_items())

    print("=" * 80)
    print("                    ANIME REFRESHER - CLI COMMAND GUIDE")
    print("=" * 80)
    print("CURRENT ACTIVE SETTINGS:")
    print(f"  Target Anime Directory:     {TARGET_DIR}")
    print(f"  SQLite Database:            {DATABASE_PATH.name} (Active)")
    print(f"  Filename Indexing:          {folder_template_str}")
    print(f"  Ignored Items:              {ignored_count} item(s)")
    print(f"  Audio Preference:           {AUDIO_PREFERENCE.upper()} (sub, dub, sub_strict, dub_strict)")
    print(f"  Preferred Resolution:       {PREFERRED_RESOLUTION}p ({', '.join(VALID_RESOLUTIONS)})")
    print(f"  AI Model File:              {MODEL_PATH.name} ({model_size}) -> {model_status}")
    print(f"  Model Download Link:        {MODEL_URL[:65]}...")
    print(f"  Automated Schedule Times:   {', '.join(SCHEDULE_TIMES)}")
    print(f"  Active Mirror Network:      {', '.join(BASE_URLS[:2])}...")
    print("=" * 80)
    print("\nHOW TO USE:")
    print("  Run this script with one or more full command-line arguments to execute actions.")
    print("  Example: python main.py --start-automation")
    print("\n" + "-" * 80)
    print("1. EXECUTION & AUTOMATION COMMANDS:")
    print("-" * 80)
    
    print("\n  --start-automation")
    print("      Description:  Searches Animepahe per-series, verifies titles, and downloads all")
    print("                    missing episodes matching your quality rules.")
    print("      Instructions: Use for standard episode syncing.")
    print("      Example:      python main.py --start-automation")

    print("\n  --start-automation-stream")
    print("      Description:  Executes the automation engine while outputting a real-time NDJSON")
    print("                    event stream on stdout for external UI frameworks (Flutter, Electron).")
    print("      Instructions: Captures live download percentages, byte counts, and failure logs.")
    print("      Example:      python main.py --start-automation-stream")

    print("\n  --preferred-resolution <RESOLUTION>")
    print("      Description:  Overrides the preferred video resolution for this run.")
    print("      Expected:     '1080', '720', '480', or '360'.")
    print("      Example:      python main.py --start-automation --preferred-resolution 720")

    print("\n  --ignore <FOLDER_OR_FILE> [<FOLDER_OR_FILE> ...]")
    print("      Description:  Adds folder names or file paths to the ignore list. Ignored items are")
    print("                    completely skipped during automation — they are never deleted, renamed,")
    print("                    or modified. The list is stored in SQLite and applied on every run.")
    print("      Standalone:   Use without --start-automation to update the ignore list for next run.")
    print("      Example:      python main.py --ignore Others")
    print("      Example:      python main.py --ignore Others \"Another Folder\" someFile.txt")

    print("\n  --list-ignored")
    print("      Description:  Displays all folders and files currently in the ignore list.")
    print("      Example:      python main.py --list-ignored")

    print("\n  --unignore <FOLDER_OR_FILE> [<FOLDER_OR_FILE> ...]")
    print("      Description:  Removes specific entries from the ignore list.")
    print("      Example:      python main.py --unignore Others")
    print("      Example:      python main.py --unignore Others \"Another Folder\"")

    print("\n  --reset-ignored")
    print("      Description:  Clears all entries from the ignore list.")
    print("      Example:      python main.py --reset-ignored")

    print("\n  --single-cycle")
    print("      Description:  Runs a single pass through the pipeline and exits immediately.")
    print("      Instructions: Ideal for automated tasks or one-off manual invocations.")
    print("      Example:      python main.py --start-automation --single-cycle")

    print("\n" + "-" * 80)
    print("2. CONFIGURATION & SETTINGS COMMANDS:")
    print("-" * 80)

    print("\n  --set-target-directory \"<DIRECTORY_PATH>\"")
    print("      Description:  Updates the anime storage directory in your .env configuration.")
    print("      Expected:     A valid absolute Windows directory path.")
    print("      Example:      python main.py --set-target-directory \"D:\\Videos\\Anime Unwatched\"")

    print("\n  --set-audio-preference <PREFERENCE>")
    print("      Description:  Sets the audio track preference when selecting video streams.")
    print("      Expected:     'sub' (default), 'dub', 'sub_strict', or 'dub_strict'.")
    print("      Example:      python main.py --set-audio-preference dub")

    print("\n  --set-preferred-resolution <RESOLUTION>")
    print("      Description:  Sets default download resolution preference in .env.")
    print("      Expected:     '1080' (default), '720', '480', or '360'.")
    print("      Example:      python main.py --set-preferred-resolution 720")

    print("\n  --download-model")
    print("      Description:  Downloads and verifies the AI model file with a live progress bar.")
    print("      Instructions: Run once during initial setup or to refresh the model file.")
    print("      Example:      python main.py --download-model")

    print("\n  --setup-task-scheduler")
    print("      Description:  Registers automated background runs in Windows Task Scheduler.")
    print("      Instructions: Schedules daily runs at your configured SCHEDULE_TIMES.")
    print("      Example:      python main.py --setup-task-scheduler")

    print("\n  --remove-task-scheduler")
    print("      Description:  Unregisters and deletes Anime Refresher scheduled tasks.")
    print("      Instructions: Disables automated background execution.")
    print("      Example:      python main.py --remove-task-scheduler")

    print("\n" + "=" * 80 + "\n")

def main():
    # If no arguments provided -> show full guide menu automatically
    if len(sys.argv) == 1:
        show_guide_menu()
        return 0

    parser = argparse.ArgumentParser(
        description="Anime Refresher - Automated Episode Synchronization Engine",
        add_help=True
    )

    # Execution Flags
    parser.add_argument("--start-automation", action="store_true", help="Searches and downloads missing anime episodes")
    parser.add_argument("--start-automation-stream", action="store_true", help="Outputs real-time type-prepended JSON stream on stdout")
    parser.add_argument("--preferred-resolution", type=str, default=None, metavar="RES", help="Overrides preferred resolution ('1080', '720', '480', '360')")
    parser.add_argument(
        "--ignore",
        dest="ignore_items",
        nargs="*",
        default=None,
        metavar="FOLDER_OR_FILE",
        help="Adds folders or files to the ignore list (saved to SQLite, applied on every automation run)"
    )
    parser.add_argument("--list-ignored", action="store_true", help="Displays all currently ignored folders and files")
    parser.add_argument(
        "--unignore",
        dest="unignore_items",
        nargs="*",
        default=None,
        metavar="FOLDER_OR_FILE",
        help="Removes specific entries from the ignore list"
    )
    parser.add_argument("--reset-ignored", action="store_true", help="Clears all entries from the ignore list")
    parser.add_argument("--single-cycle", action="store_true", help="Runs one pass and exits immediately")

    # Settings & Configuration Flags
    parser.add_argument("--set-target-directory", type=str, metavar="PATH", help="Updates target anime storage directory in .env")
    parser.add_argument("--set-audio-preference", type=str, metavar="PREF", help="Sets audio preference ('sub', 'dub', 'sub_strict', 'dub_strict')")
    parser.add_argument("--set-preferred-resolution", type=str, metavar="RES", help="Sets preferred resolution ('1080', '720', '480', '360') in .env")
    parser.add_argument("--download-model", action="store_true", help="Downloads and verifies the AI model file")
    parser.add_argument("--setup-task-scheduler", action="store_true", help="Registers automated Windows Task Scheduler triggers")
    parser.add_argument("--remove-task-scheduler", action="store_true", help="Removes automated Windows Task Scheduler triggers")

    args = parser.parse_args()

    # 1. Handle Configuration Updates
    config_action_taken = False

    if args.set_target_directory:
        target_p = Path(args.set_target_directory).resolve()
        update_env_variable("TARGET_DIR", str(target_p))
        config_action_taken = True

    if args.set_audio_preference:
        pref = args.set_audio_preference.strip().lower()
        if pref in VALID_AUDIO_PREFERENCES:
            update_env_variable("AUDIO_PREFERENCE", pref)
        else:
            print(f"[ERROR] Invalid audio preference '{pref}'. Must be one of: {', '.join(VALID_AUDIO_PREFERENCES)}")
            return 1
        config_action_taken = True

    if args.set_preferred_resolution:
        res_val = args.set_preferred_resolution.strip().lower().rstrip("p")
        if res_val in VALID_RESOLUTIONS:
            update_env_variable("PREFERRED_RESOLUTION", res_val)
        else:
            print(f"[ERROR] Invalid preferred resolution '{res_val}'. Must be one of: {', '.join(VALID_RESOLUTIONS)}")
            return 1
        config_action_taken = True


    if args.download_model:
        success = model_manager.download_model(show_progress=True)
        return 0 if success else 1

    if args.setup_task_scheduler:
        ps_script = PROJECT_DIR / "scripts" / "setup_task.ps1"
        if ps_script.exists():
            print("\n[INFO] Configuring Windows Task Scheduler...")
            res = subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(ps_script)], capture_output=True, text=True)
            print(res.stdout or res.stderr)
            return res.returncode
        else:
            print(f"[ERROR] Task setup script not found at {ps_script}")
            return 1

    if args.remove_task_scheduler:
        print("\n[INFO] Removing Anime Refresher scheduled tasks...")
        res = subprocess.run(
            ["powershell.exe", "-Command", "Get-ScheduledTask -TaskName 'AnimeRefresher_*' -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false"],
            capture_output=True, text=True
        )
        print("[OK] Scheduled tasks removed successfully.")
        return 0

    # 2. Handle Ignore List Management
    if args.list_ignored:
        current = db_manager.get_ignored_items()
        if current:
            print(f"\n[INFO] Currently ignored ({len(current)} item(s)):")
            for entry in current:
                print(f"     - {entry}")
            print()
        else:
            print("\n[INFO] The ignore list is empty.\n")
        return 0

    if args.reset_ignored:
        db_manager.clear_ignored_items()
        print("[OK] Ignore list cleared. All folders and files will be processed on the next run.")
        return 0

    if args.unignore_items is not None:
        to_remove: list = []
        for it in args.unignore_items:
            for sub in str(it).split(","):
                clean = sub.strip().strip("'\"").strip()
                if clean:
                    to_remove.append(clean)
        if not to_remove:
            print("[ERROR] --unignore requires at least one folder or file name.")
            return 1
        removed = db_manager.remove_ignored_items(to_remove)
        if removed:
            print(f"[OK] Removed {len(removed)} item(s) from ignore list:")
            for entry in removed:
                print(f"     - {entry}")
        else:
            print("[INFO] No matching items found in the ignore list.")
        remaining = db_manager.get_ignored_items()
        if remaining:
            print(f"[INFO] Remaining ignored ({len(remaining)} item(s)):")
            for entry in remaining:
                print(f"     - {entry}")
        return 0

    if config_action_taken:
        return 0

    # 3. Handle Pipeline Execution
    is_stream = args.start_automation_stream
    is_auto = args.start_automation or is_stream
    explicit_action = is_auto

    # Default to running automation if not explicitly passed but other execution flags are
    if not is_auto:
        is_auto = True

    selected_res = args.preferred_resolution.strip().lower().rstrip("p") if args.preferred_resolution else PREFERRED_RESOLUTION
    if selected_res not in VALID_RESOLUTIONS:
        selected_res = PREFERRED_RESOLUTION

    # Parse items passed via --ignore (CLI)
    cli_ignored: list = []
    if args.ignore_items is not None:
        for it in args.ignore_items:
            for sub in str(it).split(","):
                clean = sub.strip().strip("'\"").strip()
                if clean:
                    cli_ignored.append(clean)

    # Standalone --ignore: save to database and exit
    if args.ignore_items is not None and not explicit_action:
        if cli_ignored:
            added = db_manager.add_ignored_items(cli_ignored)
            print(f"[OK] Added {added} item(s) to ignore list in database:")
            for entry in cli_ignored:
                print(f"     - {entry}")
            total_items = db_manager.get_ignored_items()
            print(f"[INFO] Total ignored items: {len(total_items)}")
        else:
            print("[INFO] No items specified. Ignore list unchanged.")
        return 0

    if cli_ignored:
        db_manager.add_ignored_items(cli_ignored)

    return run_pipeline(
        start_automation=is_auto,
        stream_events=is_stream,
        single_cycle=args.single_cycle,
        preferred_resolution=selected_res,
        ignored=cli_ignored if cli_ignored else None
    )

if __name__ == "__main__":
    sys.exit(main())
