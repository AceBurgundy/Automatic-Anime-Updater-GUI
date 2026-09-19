from logging import Logger, getLogger
from os import utime
from pathlib import Path
from shutil import move as shutil_move
from time import time as current_timestamp
from typing import Dict, Optional

from httpx import Client as HttpClient, Response as HttpResponse, Timeout as HttpTimeout

from config import TEMP_DIR
from constants import DEFAULT_STALL_TIMEOUT_SECONDS
from core.safety import SafetyViolationError, safety_guard

logger: Logger = getLogger("anime_refresher.downloader")


class ResilientDownloader:
    temp_dir: Path

    def __init__(self, temp_dir: Path = TEMP_DIR) -> None:
        """
        Initialize the resilient streaming downloader.

        Parameters
        ----------
        temp_dir : Path, default=TEMP_DIR
            Directory where in-progress downloads are staged.
        """
        self.temp_dir: Path = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def get_temp_path(self, filename: str) -> Path:
        """
        Return the temporary partial download path inside the temporary directory.

        Parameters
        ----------
        filename : str
            Base target filename.

        Returns
        -------
        Path
            Path to the intermediate .partial file.
        """
        return self.temp_dir / f"{filename}.partial"

    @staticmethod
    def touch_folder_metadata(folder_path: Path) -> bool:
        """
        Update the folder's access and modified timestamps (mtime) to the current time.

        Ensures that sorting by 'Date modified' in Windows File Explorer places the folder at the top.

        Parameters
        ----------
        folder_path : Path
            Folder whose timestamps should be updated.

        Returns
        -------
        bool
            True if timestamps were updated successfully, False otherwise.
        """
        try:
            now: float = current_timestamp()
            utime(str(folder_path), (now, now))
            logger.info(f"Updated metadata timestamp for directory: {folder_path.name}")
            return True
        except Exception as timestamp_error:
            logger.warning(f"Could not update timestamp for {folder_path}: {timestamp_error}")
            return False

    def move_temp_to_target(
        self, temp_file: Path, target_dir: Path, final_filename: str
    ) -> bool:
        """
        Validate safety invariants against snapshot and move downloaded temp file to final directory.

        Also updates the target folder's modified timestamp metadata.

        Parameters
        ----------
        temp_file : Path
            Path to completed temporary download file.
        target_dir : Path
            Target destination anime series directory.
        final_filename : str
            Desired destination filename.

        Returns
        -------
        bool
            True if file was moved successfully and verified, False otherwise.
        """
        target_file: Path = target_dir / final_filename
        try:
            safety_guard.verify_write_safety(target_file)
        except SafetyViolationError as safety_error:
            logger.error(str(safety_error))
            if temp_file.exists():
                temp_file.unlink()
            return False

        if not temp_file.exists() or temp_file.stat().st_size <= 1024 * 1024:
            logger.error(f"Cannot move invalid/small temp file: {temp_file}")
            if temp_file.exists():
                temp_file.unlink()
            return False

        target_dir.mkdir(parents=True, exist_ok=True)
        file_size_megabytes: float = temp_file.stat().st_size / (1024 * 1024)
        logger.info(f"Moving validated download ({file_size_megabytes:.2f} MB) -> {target_file}")
        shutil_move(str(temp_file), str(target_file))
        self.touch_folder_metadata(target_dir)
        return True

    def download_file(
        self,
        url: str,
        target_dir: Path,
        final_filename: str,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[float] = None,
        stall_timeout: float = float(DEFAULT_STALL_TIMEOUT_SECONDS),
    ) -> bool:
        """
        Download a media stream chunk-by-chunk directly into a temporary file.

        Ensures existing files are never overwritten or modified via SafetyGuard.

        Parameters
        ----------
        url : str
            Direct HTTP streaming media URL.
        target_dir : Path
            Destination folder on local disk.
        final_filename : str
            Target video filename.
        headers : Optional[Dict[str, str]], default=None
            Custom HTTP request headers.
        cookies : Optional[Dict[str, str]], default=None
            Session cookies for the media server.
        timeout_seconds : Optional[float], default=None
            Optional maximum total read/transfer timeout in seconds (None disables wall-clock limit).
        stall_timeout : float, default=DEFAULT_STALL_TIMEOUT_SECONDS
            Maximum duration in seconds to wait for subsequent chunk packets before aborting.

        Returns
        -------
        bool
            True if downloaded, verified, and placed successfully, False otherwise.
        """
        temp_file: Path = self.temp_dir / f"{final_filename}.partial"
        target_file: Path = target_dir / final_filename

        # Programmatic Safety Guard: verify that this target file is NOT in the snapshot
        try:
            safety_guard.verify_write_safety(target_file)
        except SafetyViolationError as safety_error:
            logger.error(str(safety_error))
            return False

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        request_headers: Dict[str, str] = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Encoding": "identity;q=1, *;q=0",
            "Range": "bytes=0-",
        }
        if headers:
            request_headers.update(headers)

        logger.info(f"Starting download: {final_filename}")
        logger.debug(f"Target stream URL: {url}")
        logger.debug(f"Temporary download path: {temp_file}")
        logger.debug(f"Final destination path: {target_file}")

        try:
            if temp_file.exists():
                logger.debug(f"Removing leftover partial file: {temp_file}")
                temp_file.unlink()

            client_timeout: HttpTimeout = HttpTimeout(
                timeout_seconds,
                connect=20.0,
                read=stall_timeout,
            )
            start_time: float = current_timestamp()

            with HttpClient(
                headers=request_headers,
                cookies=cookies or {},
                follow_redirects=True,
                timeout=client_timeout,
            ) as client:
                response: HttpResponse
                with client.stream("GET", url) as response:
                    logger.debug(
                        f"Download HTTP Response: {response.status_code} {response.reason_phrase}"
                    )
                    logger.debug(
                        f"Response Content-Type: {response.headers.get('content-type', 'unknown')}"
                    )

                    if response.status_code not in (200, 206):
                        logger.error(f"Download HTTP {response.status_code} for {url}")
                        return False

                    total_bytes: int = int(response.headers.get("content-length", 0))
                    total_megabytes: float = (
                        total_bytes / (1024 * 1024) if total_bytes > 0 else 0.0
                    )
                    logger.info(
                        f"Stream size: {total_megabytes:.1f} MB"
                        if total_megabytes > 0
                        else "Stream size: chunked/unknown"
                    )

                    downloaded_bytes: int = 0
                    last_log_time: float = start_time

                    with open(temp_file, "wb") as file_handle:
                        for chunk in response.iter_bytes(chunk_size=256 * 1024):
                            if chunk:
                                file_handle.write(chunk)
                                downloaded_bytes += len(chunk)

                                now: float = current_timestamp()
                                if now - last_log_time >= 5.0:  # Log every 5 seconds
                                    elapsed: float = now - start_time
                                    speed: float = (
                                        (downloaded_bytes / (1024 * 1024)) / elapsed
                                        if elapsed > 0
                                        else 0.0
                                    )
                                    if total_bytes > 0:
                                        percentage: float = (downloaded_bytes / total_bytes) * 100
                                        logger.info(
                                            f"Progress: {percentage:.1f}% "
                                            f"({downloaded_bytes / (1024 * 1024):.1f}/{total_megabytes:.1f} MB) "
                                            f"@ {speed:.2f} MB/s"
                                        )
                                    else:
                                        logger.info(
                                            f"Progress: {downloaded_bytes / (1024 * 1024):.1f} MB downloaded "
                                            f"@ {speed:.2f} MB/s"
                                        )
                                    last_log_time = now

            duration: float = current_timestamp() - start_time
            file_size_megabytes: float = (
                temp_file.stat().st_size / (1024 * 1024) if temp_file.exists() else 0.0
            )
            average_speed: float = file_size_megabytes / duration if duration > 0 else 0.0

            # Verification of non-empty downloaded file
            if temp_file.exists() and temp_file.stat().st_size > 1024 * 1024:  # At least 1MB
                logger.info(
                    f"Download finished in {duration:.1f}s "
                    f"({file_size_megabytes:.1f} MB @ {average_speed:.2f} MB/s)."
                )
                logger.info(f"Moving {temp_file.name} -> {target_file}")
                shutil_move(str(temp_file), str(target_file))
                self.touch_folder_metadata(target_dir)
                return True
            else:
                logger.warning(
                    f"Downloaded file {temp_file} is too small ({file_size_megabytes:.2f} MB). Cleaning up."
                )
                if temp_file.exists():
                    temp_file.unlink()
                return False

        except Exception as download_error:
            logger.error(
                f"Download exception for {final_filename}: {download_error}", exc_info=True
            )
            if temp_file.exists():
                try:
                    temp_file.unlink()
                    logger.debug(f"Cleaned up partial temp file: {temp_file}")
                except Exception as delete_error:
                    logger.debug(
                        f"Failed to remove partial temp file {temp_file}: {delete_error}"
                    )
            return False
