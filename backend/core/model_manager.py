from logging import Logger, getLogger
from pathlib import Path
from shutil import move as shutil_move
from typing import Optional

from httpx import Client as HttpClient, Response as HttpResponse
from tqdm import tqdm

from config import MODEL_PATH, MODEL_URL, MODELS_DIR
from constants import MODEL_MIN_SIZE_BYTES

logger: Logger = getLogger("anime_refresher.model")


class ModelManager:
    """Manages downloading, verifying, and preparing in-process AI models."""

    model_path: Path
    model_url: str
    min_size: int
    models_dir: Path

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        model_url: str = MODEL_URL,
        min_size: int = MODEL_MIN_SIZE_BYTES,
    ) -> None:
        """
        Initialize the ModelManager with file paths and size thresholds.

        Parameters
        ----------
        model_path : Path, default=MODEL_PATH
            Destination file path for the model weights.
        model_url : str, default=MODEL_URL
            Remote URL to fetch the model from.
        min_size : int, default=MODEL_MIN_SIZE_BYTES
            Minimum expected size in bytes for model verification.
        """
        self.model_path: Path = model_path
        self.model_url: str = model_url
        self.min_size: int = min_size
        self.models_dir: Path = model_path.parent

    def is_model_present(self) -> bool:
        """
        Check if the models directory and model file exist and satisfy the minimum size requirement.

        Returns
        -------
        bool
            True if model exists on disk and meets size criteria, False otherwise.
        """
        if not self.models_dir.exists() or not self.model_path.exists():
            return False
        size: int = self.model_path.stat().st_size
        return size >= self.min_size

    def get_model_size_mb(self) -> float:
        """
        Return the model file size in Megabytes.

        Returns
        -------
        float
            Size of model file in MB, or 0.0 if not found.
        """
        if self.model_path.exists():
            return round(self.model_path.stat().st_size / (1024 * 1024), 2)
        return 0.0

    def download_model(self, url: Optional[str] = None, show_progress: bool = True) -> bool:
        """
        Download the required model file with interactive progress tracking.

        Parameters
        ----------
        url : Optional[str], default=None
            Custom download URL overriding default repository location.
        show_progress : bool, default=True
            Whether to display an interactive CLI progress bar.

        Returns
        -------
        bool
            True if downloaded and verified successfully, False otherwise.
        """
        download_url: str = url or self.model_url
        self.models_dir.mkdir(parents=True, exist_ok=True)
        temp_file: Path = self.model_path.with_suffix(".tmp")

        logger.info(f"Connecting to model repository: {download_url}")
        print(f"\n[INFO] Downloading AI model ({self.model_path.name})...")

        try:
            if temp_file.exists():
                temp_file.unlink()

            with HttpClient(follow_redirects=True, timeout=180.0) as client:
                response: HttpResponse
                with client.stream("GET", download_url) as response:
                    if response.status_code not in (200, 206):
                        logger.error(f"Failed to download model: HTTP {response.status_code}")
                        print(f"[ERROR] Model download server returned HTTP {response.status_code}")
                        return False

                    total_size: int = int(response.headers.get("content-length", 0))

                    with open(temp_file, "wb") as file_handle:
                        if show_progress and total_size > 0:
                            with tqdm(
                                total=total_size,
                                unit="B",
                                unit_scale=True,
                                unit_divisor=1024,
                                desc=self.model_path.name,
                                miniters=1,
                            ) as progress_bar:
                                for chunk in response.iter_bytes(chunk_size=128 * 1024):
                                    if chunk:
                                        file_handle.write(chunk)
                                        progress_bar.update(len(chunk))
                        else:
                            for chunk in response.iter_bytes(chunk_size=128 * 1024):
                                if chunk:
                                    file_handle.write(chunk)

            if temp_file.exists() and temp_file.stat().st_size >= self.min_size:
                if self.model_path.exists():
                    self.model_path.unlink()
                shutil_move(str(temp_file), str(self.model_path))
                size_megabytes: float = self.get_model_size_mb()
                logger.info(
                    f"Model successfully installed: {self.model_path.name} ({size_megabytes} MB)"
                )
                print(f"[OK] Model successfully installed: {self.model_path.name} ({size_megabytes} MB)")
                return True
            else:
                actual_size: int = temp_file.stat().st_size if temp_file.exists() else 0
                logger.error(
                    f"Downloaded model file incomplete ({actual_size} bytes < {self.min_size} bytes)"
                )
                print(f"[ERROR] Downloaded model file is incomplete or corrupt ({actual_size} bytes)")
                if temp_file.exists():
                    temp_file.unlink()
                return False

        except Exception as download_error:
            logger.error(f"Exception during model download: {download_error}")
            print(f"[ERROR] Failed to download model: {download_error}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def ensure_model_ready(self, auto_download: bool = False) -> bool:
        """
        Verify model presence, optionally initiating download if missing.

        Parameters
        ----------
        auto_download : bool, default=False
            Whether to trigger automated download if file is absent.

        Returns
        -------
        bool
            True if model is present or was downloaded, False otherwise.
        """
        if self.is_model_present():
            return True

        if auto_download:
            return self.download_model()

        logger.error(f"Required AI model not found at {self.model_path}")
        print("\n[ERROR] Required AI model is missing!")
        print(f"Target location: {self.model_path}")
        print("Please run the following command to download the model:")
        print("    python main.py --download-model\n")
        return False


# Global instance for shared access
model_manager: ModelManager = ModelManager()
