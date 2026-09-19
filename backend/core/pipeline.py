from asyncio import (
    TimeoutError as AsyncTimeoutError,
    run as asyncio_run,
    sleep as asyncio_sleep,
    wait_for as asyncio_wait_for,
)
from datetime import datetime, timezone
from json import dumps as json_dumps
from logging import Logger, getLogger
from pathlib import Path
from sys import stdout
from typing import Any, Dict, List, Optional, Set

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
    STALL_TIMEOUT_SECONDS,
    db_manager,
    setup_logging,
)
from core.ai_helper import AIHelper
from core.downloader import ResilientDownloader
from core.model_manager import model_manager
from core.reporter import error_reporter
from core.safety import safety_guard
from core.scanner import LocalScanner, AnimeFolder
from core.scraper import AnimepaheScraper
from core.state_manager import StateManager

logger: Logger = getLogger("anime_refresher.pipeline")

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
    error_log_message: str = "",
) -> None:
    """
    Emit a single-line type-prepended JSON event object directly to stdout with auto-flush.

    Parameters
    ----------
    anime_name : str
        Name of the anime series.
    episode_num : int
        Episode sequence number.
    filename : str
        Target filename of the episode.
    status : str
        Current download or processing status.
    progress_percentage : float, default=0.0
        Completion percentage (0.0 to 100.0).
    downloaded_bytes : int, default=0
        Number of bytes transferred.
    total_bytes : int, default=0
        Total content length in bytes.
    speed_mbps : float, default=0.0
        Instantaneous transfer speed in MB/s.
    short_error_message : str, default=""
        Summary error string for UI presentation.
    error_log_message : str, default=""
        Detailed diagnostic error log message.
    """
    payload: Dict[str, Any] = {
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
    stdout.write(json_dumps(payload, ensure_ascii=False) + "\n")
    stdout.flush()


def _render_series_box(
    index: int,
    total: int,
    folder_name: str,
    site_title: str,
    local_count: int,
    available_count: int,
    missing_count: int,
    status_note: str = "",
) -> None:
    """
    Print a clean, beautiful CLI summary card for an individual anime series.

    Parameters
    ----------
    index : int
        Current 1-based index in the iteration queue.
    total : int
        Total number of local series folders in scope.
    folder_name : str
        Local directory name of the anime.
    site_title : str
        Resolved Animepahe catalog title.
    local_count : int
        Count of local video files found.
    available_count : int
        Count of episodes available on the mirror.
    missing_count : int
        Count of episodes missing locally.
    status_note : str, default=""
        Contextual operational status note.
    """
    width: int = 76
    header: str = f" [{index:02d}/{total:02d}] {folder_name} "
    border_top: str = f"┌─{header}{'─' * max(0, width - len(header) - 3)}┐"
    border_bot: str = f"└{'─' * (width - 2)}┘"

    print(f"\n{border_top}")
    if site_title and site_title != folder_name:
        print(f'│ Site Match: "{site_title[:width - 17]}"')

    ep_info: str = f"Local: {local_count} | Available: {available_count} | Missing: {missing_count}"
    print(f"│ Episodes:   {ep_info}")
    if status_note:
        print(f"│ Status:     {status_note}")
    print(border_bot)


async def _async_pipeline(
    start_automation: bool,
    stream_events: bool,
    dry_run: bool,
    single_cycle: bool,
    maximum_downloads: Optional[int],
    preferred_resolution: str,
    headful_browser: bool,
    verbose: bool,
    ignored: Optional[List[str]] = None,
    folder_limit: Optional[int] = None,
) -> int:
    """
    Core asynchronous per-series automation pipeline implementation.

    Parameters
    ----------
    start_automation : bool
        Whether to start the automation scan and download process.
    stream_events : bool
        Whether to emit line-delimited JSON status events to stdout.
    dry_run : bool
        If True, queries and plans actions without downloading files.
    single_cycle : bool
        If True, executes exactly one pass without ongoing polling.
    maximum_downloads : Optional[int]
        Upper limit on episode downloads for this cycle.
    preferred_resolution : str
        Target resolution ('1080', '720', '480', '360').
    headful_browser : bool
        If True, launches visible browser GUI.
    verbose : bool
        Whether to enable verbose diagnostic output.
    ignored : Optional[List[str]], default=None
        Custom list of folder names or patterns to ignore.
    folder_limit : Optional[int], default=None
        Maximum count of folders to process in this run.

    Returns
    -------
    int
        Process exit code (0 for success, non-zero for failure).
    """
    headless_mode: bool = False if headful_browser else HEADLESS

    # Step 1: Arm SafetyGuard
    if not stream_events:
        logger.info("[Step 1/4] Arming SafetyGuard snapshot verification...")

    # Step 2: Verify models/ directory and AI Model presence
    if not stream_events:
        logger.info("[Step 2/4] Verifying models/ directory and AI model file integrity...")
    if not MODELS_DIR.exists() or not model_manager.is_model_present():
        logger.warning(f"AI model not found at {MODEL_PATH}. Continuing execution using deterministic regex and heuristic matching fallback.")
        if not stream_events:
            print(f"[WARNING] AI model not found in models/. Continuing execution with deterministic regex & heuristic fallback.\n")
    else:
        if not stream_events:
            logger.info("AI model verified successfully.")

    # Step 3: Scan Local Anime Collection with ignored filters
    # Combine DB ignored items and CLI ignored items
    db_ignored: List[str] = db_manager.get_ignored_items()
    effective_ignored: List[str] = list(dict.fromkeys(db_ignored + (ignored or [])))

    if not stream_events:
        logger.info(f"[Step 3/4] Scanning local unwatched anime collection in: {TARGET_DIR}")
    scanner: LocalScanner = LocalScanner(TARGET_DIR, ignored=effective_ignored)
    local_folders: List[AnimeFolder] = scanner.scan_unwatched()

    if folder_limit is not None and folder_limit > 0:
        local_folders: List[AnimeFolder] = local_folders[:folder_limit]
        if not stream_events:
            logger.info(f"[--limit] Limiting scan to first {len(local_folders)} anime directories.")

    if not stream_events:
        logger.info(f"Found {len(local_folders)} active local anime series directories.")

    # Initialize components
    ai_helper: AIHelper = AIHelper()
    downloader: ResilientDownloader = ResilientDownloader(temp_dir=TEMP_DIR)
    state_manager: StateManager = StateManager()

    # Default behavior: episodes strictly follow parent folder names (<Folder Name> <01>.<ext>)
    use_folder_as_title: bool = db_manager.get_bool_setting("folder_as_title", default=True)

    total_downloads_completed: int = 0
    consecutive_download_failures: int = 0
    consecutive_catalog_failures: int = 0
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

        for series_index, folder_obj in enumerate(local_folders, start=1):
            folder_name: str = folder_obj.name
            folder_path: Path = folder_obj.path
            existing_episodes: Set[int] = folder_obj.episode_numbers
            existing_files: List[str] = [video_file.name for video_file in folder_obj.video_files]

            # Check download cap
            if maximum_downloads is not None and total_downloads_completed >= maximum_downloads:
                if not stream_events:
                    print(f"\n[INFO] Maximum download limit ({maximum_downloads}) reached. Concluding run.")
                break

            # 1. Lookup in SQLite Series Cache
            cached: Optional[Dict[str, Any]] = db_manager.get_series_by_folder_path(folder_path)
            site_title: Optional[str] = cached.get("site_title") if cached else None
            site_session: Optional[str] = cached.get("site_session") if cached else None
            series_id: Optional[int] = cached.get("id") if cached else None

            # 2. First-time lookup: Multi-Tier Search & Candidate Ranking
            if not site_session:
                if not stream_events:
                    logger.info(f"[{series_index}/{len(local_folders)}] Resolving series mapping for: '{folder_name}'...")
                
                candidates: List[Dict[str, Any]]
                try:
                    candidates: List[Dict[str, Any]] = await asyncio_wait_for(scraper.search_anime_title(folder_name), timeout=25.0)
                except AsyncTimeoutError:
                    candidates: List[Dict[str, Any]] = []
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
                        index=series_index,
                        total=len(local_folders),
                        folder_name=folder_name,
                        site_title="Not Found on Animepahe",
                        local_count=len(existing_episodes),
                        available_count=0,
                        missing_count=0,
                        status_note="[!] No search results found (Logged to errors.html)"
                    )
                    continue

                best_candidate: Optional[Dict[str, Any]]
                best_score: float
                closest_candidate: Optional[Dict[str, Any]]
                closest_score: float
                best_candidate, best_score, closest_candidate, closest_score = ai_helper.rank_and_score_candidates(
                    folder_title=folder_name,
                    candidates=candidates,
                    threshold=0.75
                )

                if not best_candidate:
                    closest_title: str = closest_candidate.get("title", "") if closest_candidate else "None"
                    error_reporter.add_title_mismatch_error(
                        folder_name=folder_name,
                        search_query=folder_name,
                        closest_candidate=closest_title,
                        similarity_score=closest_score,
                        base_url=scraper.active_base_url
                    )
                    _render_series_box(
                        index=series_index,
                        total=len(local_folders),
                        folder_name=folder_name,
                        site_title=f"Closest: \"{closest_title}\" ({int(closest_score*100)}%)",
                        local_count=len(existing_episodes),
                        available_count=0,
                        missing_count=0,
                        status_note="[!] Title mismatch threshold not met (Logged to errors.html)"
                    )
                    continue

                # Match resolved! Persist mapping to SQLite
                site_title: Optional[str] = best_candidate.get("title", "").strip()
                site_session: Optional[str] = best_candidate.get("session", "").strip()
                series_id: Optional[int] = db_manager.upsert_series(
                    folder_path=folder_path,
                    folder_name=folder_name,
                    site_title=site_title,
                    site_session=site_session
                )

            # 3. Fetch Available Release Catalog
            play_url_target: str = f"{scraper.active_base_url}/play/{site_session}"
            catalog_episodes: Dict[int, str] = {}
            fetch_error: bool = False
            try:
                _, catalog_episodes = await asyncio_wait_for(scraper.get_show_episodes(play_url_target), timeout=45.0)
            except Exception as catalog_error:
                fetch_error: bool = True
                logger.warning(f"Could not retrieve catalog for '{folder_name}': {catalog_error}")

            if fetch_error:
                consecutive_catalog_failures += 1
                # Cloudflare Circuit Breaker: If 2+ consecutive series fail catalog retrieval
                if consecutive_catalog_failures >= 2:
                    cooldown_sec: int = 30
                    logger.warning(
                        f"Detected {consecutive_catalog_failures} consecutive catalog retrieval failures. "
                        f"Engaging Cloudflare circuit breaker: cooling down {cooldown_sec}s, purging session context, and rotating mirror..."
                    )
                    if stream_events:
                        emit_stream_event(
                            anime_name=folder_name,
                            episode_num=0,
                            filename="Circuit Breaker: Switching Mirror...",
                            status="failed",
                            progress_percentage=0.0
                        )
                    else:
                        print(f"\n   [!] Cloudflare circuit breaker engaged: resetting session & switching mirror (waiting {cooldown_sec}s)...")

                    await scraper._reset_browser_context()
                    await scraper.rotate_mirror()
                    await asyncio_sleep(cooldown_sec)
                    consecutive_catalog_failures: int = 0

                    # Retry catalog retrieval for this series on the newly rotated mirror
                    play_url_target: str = f"{scraper.active_base_url}/play/{site_session}"
                    try:
                        logger.info(f"Retrying catalog retrieval for '{folder_name}' on rotated mirror: {scraper.active_base_url}")
                        _, catalog_episodes = await asyncio_wait_for(scraper.get_show_episodes(play_url_target), timeout=45.0)
                        fetch_error: bool = False
                    except Exception as retry_err:
                        logger.warning(f"Retry on rotated mirror failed for '{folder_name}': {retry_err}")

            if not fetch_error and not catalog_episodes and len(existing_episodes) > 0:
                logger.info(
                    f"Series '{folder_name}' has {len(existing_episodes)} local episode(s) but "
                    f"catalog returned 0 releases for session '{site_session}'. "
                    f"Probing Animepahe for updated session..."
                )
                recovery_candidates: List[Dict[str, Any]]
                try:
                    recovery_candidates: List[Dict[str, Any]] = await asyncio_wait_for(scraper.search_anime_title(folder_name), timeout=25.0)
                except AsyncTimeoutError:
                    recovery_candidates: List[Dict[str, Any]] = []

                if recovery_candidates:
                    recovery_best_candidate: Optional[Dict[str, Any]]
                    recovery_best_score: float
                    recovery_best_candidate, recovery_best_score, _, _ = ai_helper.rank_and_score_candidates(
                        folder_title=folder_name,
                        candidates=recovery_candidates,
                        threshold=0.75
                    )
                    if recovery_best_candidate and recovery_best_candidate.get("session"):
                        candidate_session: str = str(recovery_best_candidate.get("session", "")).strip()
                        candidate_title: str = str(recovery_best_candidate.get("title", "")).strip() or (site_title or "")
                        # Always re-probe with the best candidate — even if the session is the same,
                        # a live attempt may succeed (transient 404 / stale session recovery).
                        probe_url: str = f"{scraper.active_base_url}/play/{candidate_session}"
                        probe_episodes: Dict[int, str] = {}
                        try:
                            _, probe_episodes = await asyncio_wait_for(
                                scraper.get_show_episodes(probe_url), timeout=45.0
                            )
                        except Exception as probe_error:
                            logger.warning(
                                f"Re-probe failed for '{folder_name}' with session "
                                f"'{candidate_session}': {probe_error}"
                            )

                        if probe_episodes:
                            logger.info(
                                f"Recovered session for '{folder_name}': "
                                f"'{site_session}' -> '{candidate_session}' — "
                                f"{len(probe_episodes)} episode(s) now available."
                            )
                            site_session: Optional[str] = candidate_session
                            site_title: Optional[str] = candidate_title
                            catalog_episodes: Dict[int, str] = probe_episodes
                            db_manager.upsert_series(
                                folder_path=folder_path,
                                folder_name=folder_name,
                                site_title=site_title,
                                site_session=site_session
                            )
                        else:
                            logger.warning(
                                f"Session re-probe returned 0 episodes for '{folder_name}' "
                                f"(candidate session: '{candidate_session}'). Skipping this run."
                            )

            missing_episodes: List[int]
            status_note: str
            if fetch_error:
                missing_episodes: List[int] = []
                status_note: str = "[!] Catalog Fetch Failed (Logged to errors.html)"
                error_reporter.add_generic_error(
                    folder_name=folder_name,
                    error_type="catalog_fetch_error",
                    message=f"Failed to retrieve episode release catalog for '{folder_name}' from {play_url_target}",
                    suggestion="Verify network/mirror connection or Cloudflare clearance on Animepahe.",
                    base_url=scraper.active_base_url
                )
            elif not catalog_episodes:
                consecutive_catalog_failures: int = 0
                missing_episodes: List[int] = []
                status_note: str = "[OK] 0 Available Episodes (Upcoming / None Released)"
            else:
                consecutive_catalog_failures: int = 0
                missing_episodes: List[int] = [episode_key for episode_key in sorted(catalog_episodes.keys()) if episode_key not in existing_episodes]
                status_note: str = "[OK] Fully Synchronized" if not missing_episodes else f"Queued {len(missing_episodes)} missing episode(s)"

            if not stream_events:
                _render_series_box(
                    index=series_index,
                    total=len(local_folders),
                    folder_name=folder_name,
                    site_title=site_title or folder_name,
                    local_count=len(existing_episodes),
                    available_count=len(catalog_episodes),
                    missing_count=len(missing_episodes),
                    status_note=status_note
                )

            # 4. Download Missing Episodes for This Series
            if start_automation and missing_episodes:
                for episode_number in missing_episodes:
                    if maximum_downloads is not None and total_downloads_completed >= maximum_downloads:
                        break

                    play_url: str = catalog_episodes[episode_number]

                    final_filename: str
                    # Deterministic vs Legacy Filename Formatting
                    if use_folder_as_title:
                        final_filename: str = ai_helper.format_folder_indexed_filename(
                            anime_folder_name=folder_name,
                            episode_num=episode_number,
                            downloaded_ext=".mp4",
                            existing_filenames=existing_files
                        )
                    else:
                        final_filename: str = ai_helper.format_sequential_filename(
                            anime_folder_name=folder_name,
                            existing_filenames=existing_files,
                            episode_num=episode_number,
                            downloaded_ext=".mp4"
                        )

                    if dry_run:
                        if not stream_events:
                            print(f"   [DRY-RUN] Would download: \"{final_filename}\"")
                        total_downloads_completed += 1
                        continue

                    print(f"   ⬇ Downloading Ep {episode_number}: \"{final_filename}\"...")
                    temp_path: Path = downloader.get_temp_path(final_filename)

                    if stream_events:
                        emit_stream_event(
                            anime_name=folder_name,
                            episode_num=episode_number,
                            filename=final_filename,
                            status="in-progress",
                            progress_percentage=0.0,
                        )

                    def on_download_progress(
                        progress_percentage: float,
                        downloaded_bytes: int,
                        total_bytes: int,
                        speed_mbps: float,
                    ) -> None:
                        """
                        Relay real-time chunk streaming progress to the stream event bus.

                        Parameters
                        ----------
                        progress_percentage : float
                            Completion percentage (0.0 to 100.0).
                        downloaded_bytes : int
                            Total bytes transferred so far.
                        total_bytes : int
                            Total stream length in bytes.
                        speed_mbps : float
                            Current transfer rate in megabytes per second.

                        Returns
                        -------
                        None
                        """
                        if stream_events:
                            emit_stream_event(
                                anime_name=folder_name,
                                episode_num=episode_number,
                                filename=final_filename,
                                status="in-progress",
                                progress_percentage=progress_percentage,
                                downloaded_bytes=downloaded_bytes,
                                total_bytes=total_bytes,
                                speed_mbps=speed_mbps,
                            )

                    download_success: bool = False
                    download_error: str = ""
                    max_download_attempts: int = 3
                    for download_attempt in range(1, max_download_attempts + 1):
                        try:
                            download_success: bool = await scraper.download_episode_to_temp(
                                anime_title=folder_name,
                                episode_num=episode_number,
                                play_url=play_url,
                                temp_target_file=temp_path,
                                preferred_resolution=preferred_resolution,
                                progress_callback=on_download_progress,
                                stall_timeout=float(STALL_TIMEOUT_SECONDS),
                            )
                            if not download_success:
                                download_error: str = "Stream resolution or transfer failed"
                        except Exception as error:
                            download_error: str = str(error)
                            download_success: bool = False

                        if download_success and temp_path.exists():
                            break

                        if download_attempt < max_download_attempts:
                            retry_delay: int = 5 * download_attempt
                            logger.warning(
                                f"Download attempt {download_attempt}/{max_download_attempts} failed for '{folder_name}' Ep {episode_number} ({download_error or 'Stream resolution failed'}). "
                                f"Cooling down {retry_delay}s before retrying..."
                            )
                            if not stream_events:
                                print(f"   [!] Attempt {download_attempt} failed ({download_error or 'Stream resolution failed'}). Retrying in {retry_delay}s...")
                            await scraper._reset_page()
                            await asyncio_sleep(retry_delay)

                    if download_success and temp_path.exists():
                        consecutive_download_failures: int = 0
                        move_success: bool = downloader.move_temp_to_target(temp_path, folder_path, final_filename)
                        if move_success:
                            total_downloads_completed += 1
                            db_manager.record_downloaded_episode(
                                series_id=series_id,
                                episode_number=episode_number,
                                filename=final_filename,
                                resolution=preferred_resolution,
                                audio=AUDIO_PREFERENCE
                            )
                            state_manager.record_downloaded_episode(folder_name, episode_number, final_filename)
                            print(f"   ✓ Saved: \"{final_filename}\"")
                            if stream_events:
                                file_size: int = (folder_path / final_filename).stat().st_size
                                emit_stream_event(
                                    anime_name=folder_name,
                                    episode_num=episode_number,
                                    filename=final_filename,
                                    status="completed",
                                    progress_percentage=100.0,
                                    downloaded_bytes=file_size,
                                    total_bytes=file_size
                                )

                            # Proactive browser hygiene: refresh page context every 5 downloads
                            if total_downloads_completed % 5 == 0:
                                logger.debug("Performing proactive browser page reset for resource hygiene...")
                                await scraper._reset_page()
                        else:
                            error_reporter.add_generic_error(
                                folder_name=folder_name,
                                error_type="move_failed",
                                message=f"Failed to move episode {episode_number} into folder under SafetyGuard validation."
                            )
                    else:
                        consecutive_download_failures += 1
                        error_reporter.add_generic_error(
                            folder_name=folder_name,
                            error_type="download_failed",
                            message=f"Failed to download episode {episode_number}: {download_error or 'Stream resolution failed'}"
                        )
                        print(f"   ✗ Download failed for Ep {episode_number}: {download_error or 'Stream resolution failed'}")

                        # If 2 or more consecutive episodes fail, trigger safety cooldown, session reset, and mirror rotation
                        if consecutive_download_failures >= 2:
                            cooldown_sec: int = 25
                            logger.warning(
                                f"Detected {consecutive_download_failures} consecutive download failures. "
                                f"Engaging safety cooldown for {cooldown_sec}s, resetting session, and rotating mirror..."
                            )
                            if not stream_events:
                                print(f"   [!] Rate limit / challenge cooldown: resetting session, switching mirror (waiting {cooldown_sec}s)...")
                            await scraper._reset_browser_context()
                            await scraper.rotate_mirror()
                            await asyncio_sleep(cooldown_sec)
                            consecutive_download_failures: int = 0

                    # Inter-download throttle
                    if REQUEST_DELAY_SECONDS > 0:
                        await asyncio_sleep(REQUEST_DELAY_SECONDS)

            await scraper.jitter(0.5, 1.0)

    # Render interactive errors.html report
    error_reporter.write_html_report(ERRORS_HTML_PATH)

    # Summary Output
    if not stream_events:
        print("\n" + "=" * 76)
        print("                      AUTOMATION RUN SUMMARY")
        print("=" * 76)
        print(f"  Episodes Downloaded:    {total_downloads_completed}")
        print(f"  Errors Recorded:        {len(error_reporter.errors)}")
        if error_reporter.has_errors():
            print(f"  Action Dashboard:       {ERRORS_HTML_PATH}")
        print("=" * 76 + "\n")

    # Record history to SQLite
    db_manager.record_run_history(
        downloaded_count=total_downloads_completed,
        error_count=len(error_reporter.errors),
        notes=f"Template: {'folder_as_title' if use_folder_as_title else 'ai_sequential'}"
    )

    return 0

def run_pipeline(
    start_automation: bool = True,
    stream_events: bool = False,
    dry_run: bool = False,
    single_cycle: bool = False,
    maximum_downloads: Optional[int] = None,
    preferred_resolution: str = PREFERRED_RESOLUTION,
    headful_browser: bool = False,
    verbose: bool = False,
    ignored: Optional[List[str]] = None,
    folder_limit: Optional[int] = None,
) -> int:
    """
    Synchronous entry point that sets up logging and runs the async pipeline.

    Parameters
    ----------
    start_automation : bool, default=True
        Whether to start the automation scan and download process.
    stream_events : bool, default=False
        Whether to emit line-delimited JSON status events to stdout.
    dry_run : bool, default=False
        If True, queries and plans actions without downloading files.
    single_cycle : bool, default=False
        If True, executes exactly one pass without ongoing polling.
    maximum_downloads : Optional[int], default=None
        Upper limit on episode downloads for this cycle.
    preferred_resolution : str, default=PREFERRED_RESOLUTION
        Target resolution ('1080', '720', '480', '360').
    headful_browser : bool, default=False
        If True, launches visible browser GUI.
    verbose : bool, default=False
        Whether to enable verbose diagnostic output.
    ignored : Optional[List[str]], default=None
        Custom list of folder names or patterns to ignore.
    folder_limit : Optional[int], default=None
        Maximum count of folders to process in this run.

    Returns
    -------
    int
        Pipeline execution exit code (0 for success, non-zero for error).
    """
    setup_logging(verbose=verbose, stream_events=stream_events)
    return asyncio_run(
        _async_pipeline(
            start_automation=start_automation,
            stream_events=stream_events,
            dry_run=dry_run,
            single_cycle=single_cycle,
            maximum_downloads=maximum_downloads,
            preferred_resolution=preferred_resolution,
            headful_browser=headful_browser,
            verbose=verbose,
            ignored=ignored,
            folder_limit=folder_limit,
        )
    )
