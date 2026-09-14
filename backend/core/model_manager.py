import logging
import shutil
from pathlib import Path
from typing import Optional
import httpx
from tqdm import tqdm

from config import MODEL_PATH, MODEL_URL, MODELS_DIR
from constants import MODEL_MIN_SIZE_BYTES

logger = logging.getLogger("anime_refresher.model")

class ModelManager:
    """Manages downloading, verifying, and preparing in-process AI models."""

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        model_url: str = MODEL_URL,
        min_size: int = MODEL_MIN_SIZE_BYTES
    ):
        self.model_path = model_path
        self.model_url = model_url
        self.min_size = min_size
        self.models_dir = model_path.parent

    def is_model_present(self) -> bool:
        """Checks if the models directory and model file exist and satisfy size requirement."""
        if not self.models_dir.exists() or not self.model_path.exists():
            return False
        size = self.model_path.stat().st_size
        return size >= self.min_size

    def get_model_size_mb(self) -> float:
        """Returns the model file size in Megabytes."""
        if self.model_path.exists():
            return round(self.model_path.stat().st_size / (1024 * 1024), 2)
        return 0.0

    def download_model(self, url: Optional[str] = None, show_progress: bool = True) -> bool:
        """Downloads the required model file with interactive progress tracking."""
        download_url = url or self.model_url
        self.models_dir.mkdir(parents=True, exist_ok=True)
        temp_file = self.model_path.with_suffix(".tmp")

        logger.info(f"Connecting to model repository: {download_url}")
        print(f"\n[INFO] Downloading AI model ({self.model_path.name})...")

        try:
            if temp_file.exists():
                temp_file.unlink()

            with httpx.Client(follow_redirects=True, timeout=180.0) as client:
                with client.stream("GET", download_url) as response:
                    if response.status_code not in (200, 206):
                        logger.error(f"Failed to download model: HTTP {response.status_code}")
                        print(f"[ERROR] Model download server returned HTTP {response.status_code}")
                        return False

                    total_size = int(response.headers.get("content-length", 0))

                    with open(temp_file, "wb") as f:
                        if show_progress and total_size > 0:
                            with tqdm(
                                total=total_size,
                                unit="B",
                                unit_scale=True,
                                unit_divisor=1024,
                                desc=self.model_path.name,
                                miniters=1,
                            ) as bar:
                                for chunk in response.iter_bytes(chunk_size=128 * 1024):
                                    if chunk:
                                        f.write(chunk)
                                        bar.update(len(chunk))
                        else:
                            for chunk in response.iter_bytes(chunk_size=128 * 1024):
                                if chunk:
                                    f.write(chunk)

            if temp_file.exists() and temp_file.stat().st_size >= self.min_size:
                if self.model_path.exists():
                    self.model_path.unlink()
                shutil.move(str(temp_file), str(self.model_path))
                size_mb = self.get_model_size_mb()
                logger.info(f"Model successfully installed: {self.model_path.name} ({size_mb} MB)")
                print(f"[OK] Model successfully installed: {self.model_path.name} ({size_mb} MB)")
                return True
            else:
                actual_size = temp_file.stat().st_size if temp_file.exists() else 0
                logger.error(f"Downloaded model file incomplete ({actual_size} bytes < {self.min_size} bytes)")
                print(f"[ERROR] Downloaded model file is incomplete or corrupt ({actual_size} bytes)")
                if temp_file.exists():
                    temp_file.unlink()
                return False

        except Exception as e:
            logger.error(f"Exception during model download: {e}")
            print(f"[ERROR] Failed to download model: {e}")
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def ensure_model_ready(self, auto_download: bool = False) -> bool:
        """Verifies model presence, optionally initiating download if missing."""
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
model_manager = ModelManager()
