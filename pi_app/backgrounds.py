from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

BACKGROUNDS_DIR = Path(__file__).parent / "static" / "backgrounds"

# HSV range that covers typical green-screen chroma green
_GREEN_LOWER = np.array([35, 50,  40])
_GREEN_UPPER = np.array([90, 255, 255])


def background_list() -> list[dict]:
    """Return available backgrounds; id='none' is always first."""
    items = [{"id": "none", "name": "None", "preview": None}]
    exts = {".jpg", ".jpeg", ".png"}
    if BACKGROUNDS_DIR.exists():
        for f in sorted(BACKGROUNDS_DIR.iterdir()):
            if f.suffix.lower() in exts:
                items.append({
                    "id": f.stem,
                    "name": f.stem.replace("_", " ").title(),
                    "preview": f"/static/backgrounds/{f.name}",
                })
    return items


def apply_background(img: Image.Image, background_id: str) -> Image.Image:
    """Chroma-key the green screen and composite onto the chosen background."""
    if background_id == "none":
        return img

    bg_path = _find_background(background_id)
    if bg_path is None:
        logger.warning("Background '%s' not found — skipping", background_id)
        return img

    # PIL → numpy RGB
    src = np.array(img.convert("RGB"))

    # Build green mask
    hsv = cv2.cvtColor(src, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, _GREEN_LOWER, _GREEN_UPPER)

    # Remove noise and close small holes in the subject silhouette
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Feather edges for a softer composite
    mask = cv2.GaussianBlur(mask, (9, 9), 0)

    # Load and resize background to match photo dimensions exactly
    bg = Image.open(bg_path).convert("RGB").resize(img.size, Image.LANCZOS)
    bg_np = np.array(bg)

    # mask=255 → green (replace with background), mask=0 → subject (keep)
    alpha = (255 - mask).astype(np.float32) / 255.0
    a3 = alpha[:, :, np.newaxis]               # broadcast across RGB channels
    composited = (src * a3 + bg_np * (1.0 - a3)).astype(np.uint8)

    return Image.fromarray(composited)


def _find_background(background_id: str) -> Path | None:
    for ext in ("jpg", "jpeg", "png"):
        p = BACKGROUNDS_DIR / f"{background_id}.{ext}"
        if p.exists():
            return p
    return None
