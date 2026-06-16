import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Set

from config import (
    TARGET_DIR,
    TEMP_DIR,
    AUDIO_PREFERENCE,
    PREFERRED_RESOLUTION,
    ERRORS_HTML_PATH,
    HEADLESS,
    BROWSER_TYPE,
    REQUEST_DELAY_SECONDS,
    MODELS_DIR,
    MODEL_PATH,
    db_manager,
    setup_logging,
)
from core.ai_helper import AIHelper
from core.downloader import ResilientDownloader
from core.model_manager import model_manager
from core.poster_manager import PosterManager
from core.reporter import error_reporter
from core.safety import safety_guard
from core.scanner import LocalScanner, AnimeFolder
from core.scraper import AnimepaheScraper
from core.state_manager import StateManager

logger = logging.getLogger("anime_refresher.pipeline")

def emit_stream_event(
    anime_name: str,
    episode_num: int,
    filename: str,
    status: str,
    progress_percentage: float = 0.0,
    downloaded_bytes: int = 0,
    total_bytes: int = 0,
    speed_mbps: float = 0.0,
    short_error_message: str = "",
    error_log_message: str = ""
) -> None:
    """Emits a single-line type-prepended JSON event object directly to stdout with auto-flush."""
    payload = {
        "string_event": "download_update",
        "string_timestamp": datetime.now(timezone.utc).isoformat(),
        "string_anime_name": str(anime_name),
        "int_episode_number": int(episode_num),
        "string_filename": str(filename),
        "string_download_status": str(status),
        "float_progress_percentage": round(float(progress_percentage), 2),
        "int_downloaded_bytes": int(downloaded_bytes),
        "int_total_bytes": int(total_bytes),
        "float_speed_mbps": round(float(speed_mbps), 2),
        "string_short_error_message": str(short_error_message),
        "string_error_log_message": str(error_log_message),
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def _render_series_box(
    index: int,
    total: int,
    folder_name: str,
    site_title: str,
    local_count: int,
    available_count: int,
    missing_count: int,
    poster_status: str,
    status_note: str = ""
) -> None:
    """Prints a clean, beautiful CLI summary card for an individual anime series."""
    width = 76
    header = f" [{index:02d}/{total:02d}] {folder_name} "
    border_top = f"┌─{header}{'─' * max(0, width - len(header) - 3)}┐"
    border_bot = f"└{'─' * (width - 2)}┘"

    print(f"\n{border_top}")
    if site_title and site_title != folder_name:
        print(f"│ Site Match: \"{site_title[:width - 17]}\"")
    
    ep_info = f"Local: {local_count} | Available: {available_count} | Missing: {missing_count}"
    print(f"│ Episodes:   {ep_info}")
    print(f"│ Artwork:    {poster_status}")
    if status_note:
        print(f"│ Status:     {status_note}")
    print(border_bot)

async def _async_pipeline(
    start_automation: bool,
    synchronize_posters: bool,
    stream_events: bool,
    dry_run: bool,
    single_cycle: bool,
    maximum_downloads: Optional[int],
    preferred_resolution: str,
    headful_browser: bool,
    verbose: bool,
    ignored: Optional[List[str]] = None
) -> int:
    """Core asynchronous per-series automation pipeline implementation."""
    headless_mode = False if headful_browser else HEADLESS

    # Step 1: Arm SafetyGuard
    if not stream_events:
        logger.info("[Step 1/4] Arming SafetyGuard snapshot verification...")

    # Step 2: Verify models/ directory and AI Model presence
    if not stream_events:
        logger.info("[Step 2/4] Verifying models/ directory and AI model file integrity...")
    if not MODELS_DIR.exists() or not model_manager.is_model_present():
        logger.error("Automation halted: models/ directory or required AI model file does not exist.")
        print("\n[ERROR] Automation halted: models/ directory or required AI model file does not exist!")
        print(f"Target location: {MODEL_PATH}")
        print("Please run 'python main.py --download-model' to install the required model before running automation.\n")
        if stream_events:
            emit_stream_event(
                anime_name="System",
                episode_num=0,
                filename="",
                status="failed",
                short_error_message="models/ directory or required AI model file does not exist",
                error_log_message="Please run 'python main.py --download-model' to install the model before running automation."
            )
        return 1

    # Step 3: Scan Local Anime Collection with ignored filters
    # Combine DB ignored items and CLI ignored items
    db_ignored = db_manager.get_ignored_items()
    effective_ignored = list(dict.fromkeys(db_ignored + (ignored or [])))

    if not stream_events:
        logger.info(f"[Step 3/4] Scanning local unwatched anime collection in: {TARGET_DIR}")
    scanner = LocalScanner(TARGET_DIR, ignored=effective_ignored)
    local_folders = scanner.scan_unwatched()

    if not stream_events:
        logger.info(f"Found {len(local_folders)} active local anime series directories.")

    # Initialize components
    ai_helper = AIHelper()
    downloader = ResilientDownloader(temp_dir=TEMP_DIR)
    poster_manager = PosterManager()
    state_manager = StateManager()

    # Read folder_as_title preference from SQLite (default is True)
    use_folder_as_title = db_manager.get_bool_setting("folder_as_title", default=True)

    total_downloads_completed = 0
    total_posters_saved = 0
    error_reporter.clear()

    # Step 4: Iterative Per-Series Automation Loop
    if not stream_events:
        logger.info("\n[Step 4/4] Starting per-series synchronization engine...")

    async with AnimepaheScraper(
        state_manager=state_manager,
        headless=headless_mode,
        browser_type=BROWSER_TYPE,
        audio_preference=AUDIO_PREFERENCE,
        preferred_resolution=preferred_resolution
    ) as scraper:
        await scraper.find_active_mirror()

        for idx, folder_obj in enumerate(local_folders, start=1):
            folder_name = folder_obj.name
            folder_path = folder_obj.path
            existing_eps = folder_obj.episode_numbers
            existing_files = [f.name for f in folder_obj.video_files]

            # Check download cap
            if maximum_downloads is not None and total_downloads_completed >= maximum_downloads:
                if not stream_events:
                    print(f"\n[INFO] Maximum download limit ({maximum_downloads}) reached. Concluding run.")
                break

            # 1. Lookup in SQLite Series Cache
            cached = db_manager.get_series_by_folder_path(folder_path)
            site_title = cached.get("site_title") if cached else None
            site_session = cached.get("site_session") if cached else None
            poster_url = cached.get("poster_url") if cached else None
            series_id = cached.get("id") if cached else None

            # 2. First-time lookup: Multi-Tier Search & Candidate Ranking
            if not site_session:
                if not stream_events:
                    logger.info(f"[{idx}/{len(local_folders)}] Resolving series mapping for: '{folder_name}'...")
                
                try:
                    candidates = await asyncio.wait_for(scraper.search_anime_title(folder_name), timeout=25.0)
                except asyncio.TimeoutError:
                    candidates = []
                    logger.warning(f"Search timed out (25s) for '{folder_name}'")

                if not candidates:
                    error_reporter.add_title_mismatch_error(
                        folder_name=folder_name,
                        search_query=folder_name,
                        closest_candidate="",
                        similarity_score=0.0,
                        base_url=scraper.active_base_url
                    )
                    _render_series_box(
                        index=idx,
                        total=len(local_folders),
                        folder_name=folder_name,
                        site_title="Not Found on Animepahe",
                        local_count=len(existing_eps),
                        available_count=0,
                        missing_count=0,
                        poster_status="Skipped",
                        status_note="[!] No search results found (Logged to errors.html)"
                    )
                    continue

                best_cand, best_score, closest_cand, closest_score = ai_helper.rank_and_score_candidates(
                    folder_title=folder_name,
                    candidates=candidates,
                    threshold=0.75
                )

                if not best_cand:
                    closest_title = closest_cand.get("title", "") if closest_cand else "None"
                    error_reporter.add_title_mismatch_error(
                        folder_name=folder_name,
                        search_query=folder_name,
                        closest_candidate=closest_title,
                        similarity_score=closest_score,
                        base_url=scraper.active_base_url
                    )
                    _render_series_box(
                        index=idx,
                        total=len(local_folders),
                        folder_name=folder_name,
                        site_title=f"Closest: \"{closest_title}\" ({int(closest_score*100)}%)",
                        local_count=len(existing_eps),
                        available_count=0,
                        missing_count=0,
                        poster_status="Skipped",
                        status_note="[!] Title mismatch threshold not met (Logged to errors.html)"
                    )
                    continue

                # Match resolved! Persist mapping to SQLite
                site_title = best_cand.get("title", "").strip()
                site_session = best_cand.get("session", "").strip()
                poster_url = best_cand.get("poster", "").strip()
                series_id = db_manager.upsert_series(
                    folder_path=folder_path,
                    folder_name=folder_name,
                    site_title=site_title,
                    site_session=site_session,
                    poster_url=poster_url
                )

            # 3. Synchronize Poster Artwork if requested
            has_existing_poster = poster_manager.has_poster(folder_path)
            if has_existing_poster:
                poster_status_msg = "[OK] Present"
            elif not synchronize_posters:
                poster_status_msg = "Missing (Run --synchronize-posters)"
            else:
                if dry_run:
                    poster_status_msg = "[DRY-RUN] Would download poster.png"
                else:
                    poster_bytes = await scraper.fetch_poster_for_anime(
                        anime_session_or_id=site_session,
                        poster_url=poster_url
                    )
                    if poster_bytes:
                        saved = poster_manager.save_poster_from_bytes(poster_bytes, folder_path)
                        if saved:
                            total_posters_saved += 1
                            db_manager.mark_poster_downloaded(series_id, True)
                            poster_status_msg = "[OK] Saved poster.png"
                        else:
                            poster_status_msg = "[!] Poster save failed"
                    else:
                        poster_status_msg = "[!] Poster download failed"


            # 4. Fetch Available Release Catalog
            play_url_target = f"{scraper.active_base_url}/play/{site_session}"
            catalog_episodes: Dict[int, str] = {}
            fetch_error = False
            try:
                _, catalog_episodes = await asyncio.wait_for(scraper.get_show_episodes(play_url_target), timeout=45.0)
            except Exception as e:
                fetch_error = True
                logger.warning(f"Could not retrieve catalog for '{folder_name}': {e}")

            if not catalog_episodes and (fetch_error or len(existing_eps) > 0):
                missing_eps = []
                status_note = "[!] Catalog Fetch Failed (Logged to errors.html)"
                error_reporter.add_generic_error(
                    folder_name=folder_name,
                    error_type="catalog_fetch_error",
                    message=f"Failed to retrieve episode release catalog for '{folder_name}' from {play_url_target}",
                    suggestion="Verify network/mirror connection or Cloudflare clearance on Animepahe.",
                    base_url=scraper.active_base_url
                )
            else:
                missing_eps = [ep for ep in sorted(catalog_episodes.keys()) if ep not in existing_eps]
                status_note = "[OK] Fully Synchronized" if not missing_eps else f"Queued {len(missing_eps)} missing episode(s)"

            if not stream_events:
                _render_series_box(
                    index=idx,
                    total=len(local_folders),
                    folder_name=folder_name,
                    site_title=site_title or folder_name,
                    local_count=len(existing_eps),
                    available_count=len(catalog_episodes),
                    missing_count=len(missing_eps),
                    poster_status=poster_status_msg,
                    status_note=status_note
                )

            # 5. Download Missing Episodes for This Series
            if start_automation and missing_eps:
                for ep_num in missing_eps:
                    if maximum_downloads is not None and total_downloads_completed >= maximum_downloads:
                        break

                    play_url = catalog_episodes[ep_num]

                    # Deterministic vs Legacy Filename Formatting
                    if use_folder_as_title:
                        final_filename = ai_helper.format_folder_indexed_filename(
                            anime_folder_name=folder_name,
                            episode_num=ep_num,
                            downloaded_ext=".mp4",
                            existing_filenames=existing_files
                        )
                    else:
                        final_filename = ai_helper.format_sequential_filename(
                            anime_folder_name=folder_name,
                            existing_filenames=existing_files,
                            episode_num=ep_num,
                            downloaded_ext=".mp4"
                        )

                    if dry_run:
                        if not stream_events:
                            print(f"   [DRY-RUN] Would download: \"{final_filename}\"")
                        total_downloads_completed += 1
                        continue

                    print(f"   ⬇ Downloading Ep {ep_num}: \"{final_filename}\"...")
                    temp_path = downloader.get_temp_path(final_filename)

                    if stream_events:
                        emit_stream_event(
                            anime_name=folder_name,
                            episode_num=ep_num,
                            filename=final_filename,
                            status="in-progress",
                            progress_percentage=0.0
                        )

                    dl_success = False
                    dl_error = ""
                    try:
                        dl_success = await asyncio.wait_for(
                            scraper.download_episode_to_temp(
                                anime_title=folder_name,
                                episode_num=ep_num,
                                play_url=play_url,
                                temp_target_file=temp_path,
                                preferred_resolution=preferred_resolution
                            ),
                            timeout=300.0
                        )
                    except asyncio.TimeoutError:
                        dl_error = "Download timed out (300s)"
                    except Exception as err:
                        dl_error = str(err)

                    if dl_success and temp_path.exists():
                        move_success = downloader.move_temp_to_target(temp_path, folder_path, final_filename)
                        if move_success:
                            total_downloads_completed += 1
                            db_manager.record_downloaded_episode(
                                series_id=series_id,
                                episode_number=ep_num,
                                filename=final_filename,
                                resolution=preferred_resolution,
                                audio=AUDIO_PREFERENCE
                            )
                            state_manager.record_downloaded_episode(folder_name, ep_num, final_filename)
                            print(f"   ✓ Saved: \"{final_filename}\"")
                            if stream_events:
                                file_size = (folder_path / final_filename).stat().st_size
                                emit_stream_event(
                                    anime_name=folder_name,
                                    episode_num=ep_num,
                                    filename=final_filename,
                                    status="completed",
                                    progress_percentage=100.0,
                                    downloaded_bytes=file_size,
                                    total_bytes=file_size
                                )
                        else:
                            error_reporter.add_generic_error(
                                folder_name=folder_name,
                                error_type="move_failed",
                                message=f"Failed to move episode {ep_num} into folder under SafetyGuard validation."
                            )
                    else:
                        error_reporter.add_generic_error(
                            folder_name=folder_name,
                            error_type="download_failed",
                            message=f"Failed to download episode {ep_num}: {dl_error or 'Stream resolution failed'}"
                        )
                        print(f"   ✗ Download failed for Ep {ep_num}: {dl_error or 'Stream resolution failed'}")

                    # Inter-download throttle
                    if REQUEST_DELAY_SECONDS > 0:
                        await asyncio.sleep(REQUEST_DELAY_SECONDS)

            await scraper.jitter(0.5, 1.0)

    # Render interactive errors.html report
    error_reporter.write_html_report(ERRORS_HTML_PATH)

    # Summary Output
    if not stream_events:
        print("\n" + "=" * 76)
        print("                      AUTOMATION RUN SUMMARY")
        print("=" * 76)
        print(f"  Episodes Downloaded:    {total_downloads_completed}")
        print(f"  Posters Synchronized:   {total_posters_saved}")
        print(f"  Errors Recorded:        {len(error_reporter.errors)}")
        if error_reporter.has_errors():
            print(f"  Action Dashboard:       {ERRORS_HTML_PATH}")
        print("=" * 76 + "\n")

    # Record history to SQLite
    db_manager.record_run_history(
        downloaded_count=total_downloads_completed,
        error_count=len(error_reporter.errors),
        notes=f"Posters: {total_posters_saved}, Template: {'folder_as_title' if use_folder_as_title else 'ai_sequential'}"
    )

    return 0

def run_pipeline(
    start_automation: bool = True,
    synchronize_posters: bool = False,
    stream_events: bool = False,
    dry_run: bool = False,
    single_cycle: bool = False,
    maximum_downloads: Optional[int] = None,
    preferred_resolution: str = PREFERRED_RESOLUTION,
    headful_browser: bool = False,
    verbose: bool = False,
    ignored: Optional[List[str]] = None
) -> int:
    """Synchronous entry point that sets up logging and runs the async pipeline."""
    setup_logging(verbose=verbose, stream_events=stream_events)
    return asyncio.run(
        _async_pipeline(
            start_automation=start_automation,
            synchronize_posters=synchronize_posters,
            stream_events=stream_events,
            dry_run=dry_run,
            single_cycle=single_cycle,
            maximum_downloads=maximum_downloads,
            preferred_resolution=preferred_resolution,
            headful_browser=headful_browser,
            verbose=verbose,
            ignored=ignored
        )
    )
