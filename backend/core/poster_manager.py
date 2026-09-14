import io
import logging
import shutil
import time
from pathlib import Path
from typing import List, Optional
from PIL import Image

from constants import POSTER_FILENAME
from core.safety import safety_guard, SafetyViolationError
from core.scanner import AnimeFolder
from config import TEMP_DIR

logger = logging.getLogger("anime_refresher.poster")

class PosterManager:
    """Manages detection, conversion, and safe writing of anime poster artwork."""

    def __init__(self, poster_filename: str = POSTER_FILENAME):
        self.poster_filename = poster_filename

    def has_poster(self, folder_path: Path) -> bool:
        """Checks if a poster or cover image already exists in the folder."""
        if not folder_path.exists() or not folder_path.is_dir():
            return False

        # Primary target check
        if (folder_path / self.poster_filename).exists():
            return True

        # Check common cover/poster image variants
        for variant in ("poster.jpg", "poster.webp", "cover.png", "cover.jpg", "folder.jpg", "folder.png"):
            if (folder_path / variant).exists():
                return True

        return False

    def get_folders_needing_posters(self, folders: List[AnimeFolder]) -> List[AnimeFolder]:
        """Filters anime folders that currently lack a poster image."""
        needing = []
        for f in folders:
            if not self.has_poster(f.path):
                needing.append(f)
        return needing

    def save_poster_from_bytes(self, image_bytes: bytes, target_dir: Path) -> bool:
        """Converts image bytes of any format to standard PNG and writes safely."""
        if not image_bytes or len(image_bytes) < 1000:
            logger.warning(f"Invalid image bytes provided for poster in {target_dir.name}")
            return False

        target_file = target_dir / self.poster_filename

        try:
            safety_guard.verify_write_safety(target_file)
        except SafetyViolationError as e:
            logger.error(str(e))
            return False

        temp_poster_path = TEMP_DIR / f"poster_{int(time.time() * 1000)}.png"

        try:
            # Open with Pillow from in-memory byte buffer
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert color mode: Preserve RGBA transparency if present, otherwise convert to RGB
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    converted = img.convert("RGBA")
                else:
                    converted = img.convert("RGB")

                # Save as PNG to temporary file
                temp_poster_path.parent.mkdir(parents=True, exist_ok=True)
                converted.save(temp_poster_path, format="PNG", optimize=True)

            if temp_poster_path.exists() and temp_poster_path.stat().st_size > 500:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_poster_path), str(target_file))
                logger.info(f"Saved poster: {target_file.name} in {target_dir.name}")
                return True
            else:
                logger.error(f"Generated temp poster was empty or missing for {target_dir.name}")
                return False

        except Exception as e:
            logger.error(f"Failed to convert/save poster for {target_dir.name}: {e}")
            if temp_poster_path.exists():
                try:
                    temp_poster_path.unlink()
                except Exception:
                    pass
            return False
