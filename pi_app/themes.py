"""Photo frame / theme compositing using Pillow.

Each theme function receives the raw captured Image and returns a new Image
(possibly larger due to border padding). An optional `frame_color` tuple
overrides the border colour so it can be matched to the chosen background.
The CSS live preview in index.html mirrors the visual style.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageEnhance

Color = tuple[int, int, int]


def _text_color(bg: Color) -> Color:
    """Return black or white depending on background luminance."""
    lum = 0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]
    return (30, 30, 30) if lum > 128 else (225, 225, 225)


# ── Theme implementations ────────────────────────────────────────────────────

def _apply_none(img: Image.Image, frame_color: Color | None = None) -> Image.Image:
    return img


def _apply_classic(img: Image.Image, frame_color: Color | None = None) -> Image.Image:
    """Polaroid frame — even border on three sides, wider at bottom."""
    color = frame_color or (255, 255, 255)
    w, h = img.size
    bx = int(w * 0.06)
    bt = int(h * 0.06)
    bb = int(h * 0.20)

    out = Image.new("RGB", (w + bx * 2, h + bt + bb), color)
    out.paste(img, (bx, bt))

    draw = ImageDraw.Draw(out)
    label = "PHOTOBOOTH"
    tx = (out.width - len(label) * 6) // 2
    ty = h + bt + (bb - 18) // 2
    draw.text((tx, ty), label, fill=_text_color(color))
    return out


def _apply_birthday(img: Image.Image, frame_color: Color | None = None) -> Image.Image:
    """Rainbow stripe border. frame_color tints the palette when provided."""
    w, h = img.size
    pad = int(min(w, h) * 0.06)

    base_colors: list[Color] = [
        (255, 107, 107),
        (255, 217,  61),
        (107, 203, 119),
        ( 77, 150, 255),
        (255, 107, 206),
    ]

    if frame_color:
        # Blend each stripe 40 % toward the dominant background colour
        fr, fg, fb = frame_color
        colors = [
            (int(r * 0.6 + fr * 0.4), int(g * 0.6 + fg * 0.4), int(b * 0.6 + fb * 0.4))
            for r, g, b in base_colors
        ]
    else:
        colors = base_colors

    out = Image.new("RGB", (w + pad * 2, h + pad * 2), (255, 255, 255))
    draw = ImageDraw.Draw(out)

    sw = out.width // len(colors) + 1
    for i, c in enumerate(colors):
        x0, x1 = i * sw, (i + 1) * sw
        draw.rectangle([(x0, 0),       (x1, pad)],         fill=c)
        draw.rectangle([(x0, h + pad), (x1, out.height)],  fill=c)

    sh = out.height // len(colors) + 1
    for i, c in enumerate(colors):
        y0, y1 = i * sh, (i + 1) * sh
        draw.rectangle([(0,       y0), (pad,       y1)], fill=c)
        draw.rectangle([(w + pad, y0), (out.width, y1)], fill=c)

    out.paste(img, (pad, pad))
    return out


def _apply_vintage(img: Image.Image, frame_color: Color | None = None) -> Image.Image:
    """Sepia + reduced contrast + warm border."""
    gray = img.convert("L")
    sepia = Image.merge("RGB", [
        gray.point(lambda x: min(255, int(x * 1.08))),
        gray.point(lambda x: min(255, int(x * 0.86))),
        gray.point(lambda x: min(255, int(x * 0.67))),
    ])
    sepia = ImageEnhance.Contrast(sepia).enhance(0.85)

    border_color = frame_color or (160, 128, 88)
    w, h = sepia.size
    pad = int(min(w, h) * 0.06)
    out = Image.new("RGB", (w + pad * 2, h + pad * 2), border_color)
    out.paste(sepia, (pad, pad))
    return out


# ── Registry ─────────────────────────────────────────────────────────────────

THEMES: dict[str, dict] = {
    "none":     {"name": "Original",  "apply": _apply_none,     "preview": "#6c757d"},
    "classic":  {"name": "Classic",   "apply": _apply_classic,  "preview": "#ffffff"},
    "birthday": {"name": "Birthday",  "apply": _apply_birthday, "preview": "#ffd93d"},
    "vintage":  {"name": "Vintage",   "apply": _apply_vintage,  "preview": "#c8a876"},
}


def apply_theme(
    img: Image.Image,
    theme_id: str,
    frame_color: Color | None = None,
) -> Image.Image:
    fn = THEMES.get(theme_id, THEMES["none"])["apply"]
    return fn(img, frame_color=frame_color)


def theme_list() -> list[dict]:
    return [{"id": k, "name": v["name"], "preview": v["preview"]} for k, v in THEMES.items()]
