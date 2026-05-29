"""Photo frame / theme compositing using Pillow.

Each theme function receives the raw captured Image and returns a new Image
(possibly larger due to border padding). The CSS preview in index.html mirrors
the visual style so the user sees a live preview before shooting.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageEnhance


# ── Theme implementations ────────────────────────────────────────────────────

def _apply_none(img: Image.Image) -> Image.Image:
    return img


def _apply_classic(img: Image.Image) -> Image.Image:
    """White polaroid frame — even border on three sides, wider at bottom."""
    w, h = img.size
    bx = int(w * 0.06)
    bt = int(h * 0.06)
    bb = int(h * 0.20)

    out = Image.new("RGB", (w + bx * 2, h + bt + bb), (255, 255, 255))
    out.paste(img, (bx, bt))

    draw = ImageDraw.Draw(out)
    label = "PHOTOBOOTH"
    tx = (out.width - len(label) * 6) // 2
    ty = h + bt + (bb - 18) // 2
    draw.text((tx, ty), label, fill=(185, 185, 185))
    return out


def _apply_birthday(img: Image.Image) -> Image.Image:
    """Rainbow stripe border — festive multicolor frame."""
    w, h = img.size
    pad = int(min(w, h) * 0.06)
    colors = [
        (255, 107, 107),  # coral
        (255, 217,  61),  # yellow
        (107, 203, 119),  # green
        ( 77, 150, 255),  # blue
        (255, 107, 206),  # pink
    ]

    out = Image.new("RGB", (w + pad * 2, h + pad * 2), (255, 255, 255))
    draw = ImageDraw.Draw(out)

    # top / bottom horizontal stripes
    sw = out.width // len(colors) + 1
    for i, c in enumerate(colors):
        x0, x1 = i * sw, (i + 1) * sw
        draw.rectangle([(x0, 0),       (x1, pad)],            fill=c)
        draw.rectangle([(x0, h + pad), (x1, out.height)],     fill=c)

    # left / right vertical stripes
    sh = out.height // len(colors) + 1
    for i, c in enumerate(colors):
        y0, y1 = i * sh, (i + 1) * sh
        draw.rectangle([(0,       y0), (pad,          y1)],   fill=c)
        draw.rectangle([(w + pad, y0), (out.width,    y1)],   fill=c)

    out.paste(img, (pad, pad))
    return out


def _apply_vintage(img: Image.Image) -> Image.Image:
    """Sepia + reduced contrast + warm brown border."""
    gray = img.convert("L")
    sepia = Image.merge("RGB", [
        gray.point(lambda x: min(255, int(x * 1.08))),
        gray.point(lambda x: min(255, int(x * 0.86))),
        gray.point(lambda x: min(255, int(x * 0.67))),
    ])
    sepia = ImageEnhance.Contrast(sepia).enhance(0.85)

    w, h = sepia.size
    pad = int(min(w, h) * 0.06)
    out = Image.new("RGB", (w + pad * 2, h + pad * 2), (160, 128, 88))
    out.paste(sepia, (pad, pad))
    return out


# ── Registry ─────────────────────────────────────────────────────────────────

THEMES: dict[str, dict] = {
    "none":     {"name": "Original",  "apply": _apply_none,     "preview": "#6c757d"},
    "classic":  {"name": "Classic",   "apply": _apply_classic,  "preview": "#ffffff"},
    "birthday": {"name": "Birthday",  "apply": _apply_birthday, "preview": "#ffd93d"},
    "vintage":  {"name": "Vintage",   "apply": _apply_vintage,  "preview": "#c8a876"},
}


def apply_theme(img: Image.Image, theme_id: str) -> Image.Image:
    return THEMES.get(theme_id, THEMES["none"])["apply"](img)


def theme_list() -> list[dict]:
    return [{"id": k, "name": v["name"], "preview": v["preview"]} for k, v in THEMES.items()]
