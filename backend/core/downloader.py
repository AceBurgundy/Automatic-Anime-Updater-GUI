import logging
import shutil
import time
from pathlib import Path
from typing import Dict, Optional
import httpx
from config import TEMP_DIR
from core.safety import safety_guard, SafetyViolationError

logger = logging.getLogger("anime_refresher.downloader")

class ResilientDownloader:
    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_temp_path(self, filename: str) -> Path:
        """Returns the temporary partial download path inside %TEMP%\\anime-refresher."""
        return self.temp_dir / f"{filename}.partial"

    def move_temp_to_target(self, temp_file: Path, target_dir: Path, final_filename: str) -> bool:
        """
        Validates safety invariants against snapshot and moves downloaded temp file to final directory.
        """
        target_file = target_dir / final_filename
        try:
            safety_guard.verify_write_safety(target_file)
        except SafetyViolationError as e:
            logger.error(str(e))
            if temp_file.exists():
                temp_file.unlink()
            return False

        if not temp_file.exists() or temp_file.stat().st_size <= 1024 * 1024:
            logger.error(f"Cannot move invalid/small temp file: {temp_file}")
            if temp_file.exists():
                temp_file.unlink()
            return False

        target_dir.mkdir(parents=True, exist_ok=True)
        file_size_mb = temp_file.stat().st_size / (1024 * 1024)
        logger.info(f"Moving validated download ({file_size_mb:.2f} MB) -> {target_file}")
        shutil.move(str(temp_file), str(target_file))
        return True

    def download_file(
        self,
        url: str,
        target_dir: Path,
        final_filename: str,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout_seconds: float = 300.0
    ) -> bool:
        """
        Streams a video file into temp directory and moves it to target_dir upon completion.
        Cleans up partial files on any failure or timeout.
        Ensures existing files are never overwritten or modified via SafetyGuard.
        """
        temp_file = self.temp_dir / f"{final_filename}.partial"
        target_file = target_dir / final_filename

        # Programmatic Safety Guard: verify that this target file is NOT in the snapshot
        try:
            safety_guard.verify_write_safety(target_file)
        except SafetyViolationError as e:
            logger.error(str(e))
            return False

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "identity;q=1, *;q=0",
            "Range": "bytes=0-",
        }
        if headers:
            req_headers.update(headers)

        logger.info(f"Starting download: {final_filename}")
        logger.debug(f"Target stream URL: {url}")
        logger.debug(f"Temporary download path: {temp_file}")
        logger.debug(f"Final destination path: {target_file}")

        try:
            if temp_file.exists():
                logger.debug(f"Removing leftover partial file: {temp_file}")
                temp_file.unlink()

            client_timeout = httpx.Timeout(timeout_seconds, connect=20.0, read=30.0)
            start_time = time.time()

            with httpx.Client(
                headers=req_headers,
                cookies=cookies or {},
                follow_redirects=True,
                timeout=client_timeout
            ) as client:
                with client.stream("GET", url) as response:
                    logger.debug(f"Download HTTP Response: {response.status_code} {response.reason_phrase}")
                    logger.debug(f"Response Content-Type: {response.headers.get('content-type', 'unknown')}")

                    if response.status_code not in (200, 206):
                        logger.error(f"Download HTTP {response.status_code} for {url}")
                        return False

                    total_bytes = int(response.headers.get("content-length", 0))
                    total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0
                    logger.info(f"Stream size: {total_mb:.1f} MB" if total_mb > 0 else "Stream size: chunked/unknown")

                    downloaded_bytes = 0
                    last_log_time = start_time

                    with open(temp_file, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=256 * 1024):
                            if chunk:
                                f.write(chunk)
                                downloaded_bytes += len(chunk)

                                now = time.time()
                                if now - last_log_time >= 5.0:  # Log every 5 seconds
                                    elapsed = now - start_time
                                    speed = (downloaded_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                                    if total_bytes > 0:
                                        pct = (downloaded_bytes / total_bytes) * 100
                                        logger.info(f"Progress: {pct:.1f}% ({downloaded_bytes / (1024*1024):.1f}/{total_mb:.1f} MB) @ {speed:.2f} MB/s")
                                    else:
                                        logger.info(f"Progress: {downloaded_bytes / (1024*1024):.1f} MB downloaded @ {speed:.2f} MB/s")
                                    last_log_time = now

            duration = time.time() - start_time
            file_size_mb = temp_file.stat().st_size / (1024 * 1024) if temp_file.exists() else 0
            avg_speed = file_size_mb / duration if duration > 0 else 0

            # Verification of non-empty downloaded file
            if temp_file.exists() and temp_file.stat().st_size > 1024 * 1024:  # At least 1MB
                logger.info(f"Download finished in {duration:.1f}s ({file_size_mb:.1f} MB @ {avg_speed:.2f} MB/s).")
                logger.info(f"Moving {temp_file.name} -> {target_file}")
                shutil.move(str(temp_file), str(target_file))
                return True
            else:
                logger.warning(f"Downloaded file {temp_file} is too small ({file_size_mb:.2f} MB). Cleaning up.")
                if temp_file.exists():
                    temp_file.unlink()
                return False

        except Exception as e:
            logger.error(f"Download exception for {final_filename}: {e}", exc_info=True)
            if temp_file.exists():
                try:
                    temp_file.unlink()
                    logger.debug(f"Cleaned up partial temp file: {temp_file}")
                except Exception as del_err:
                    logger.debug(f"Failed to remove partial temp file {temp_file}: {del_err}")
            return False
