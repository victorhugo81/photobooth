"""Generate sample background images for the green-screen feature.

Run once from inside pi_app/:
    uv run python create_sample_backgrounds.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).parent / "static" / "backgrounds"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1280, 960


def save(name: str, img: Image.Image) -> None:
    p = OUT / f"{name}.jpg"
    img.convert("RGB").save(p, "JPEG", quality=90)
    print(f"  wrote {p}")


# ── Galaxy ───────────────────────────────────────────────────────────────────
def make_galaxy() -> Image.Image:
    rng = np.random.default_rng(42)
    arr = np.zeros((H, W, 3), dtype=np.uint8)

    # Deep-blue-to-purple vertical gradient
    for y in range(H):
        t = y / H
        arr[y, :] = [int(8 + t * 25), int(4 + t * 8), int(40 + t * 55)]

    # Faint nebula blobs
    img = Image.fromarray(arr)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for cx, cy, r, col in [
        (300, 400, 200, (80, 0, 140, 60)),
        (900, 200, 180, (0, 60, 160, 50)),
        (700, 700, 150, (120, 20, 80, 40)),
    ]:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=col)
    overlay = overlay.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    arr = np.array(img)

    # Stars: small bright dots
    n = 900
    xs = rng.integers(0, W, n)
    ys = rng.integers(0, H, n)
    br = rng.integers(160, 255, n)
    sizes = rng.choice([1, 1, 1, 2], n)
    for x, y, b, s in zip(xs, ys, br, sizes):
        arr[max(0, y - s):y + s + 1, max(0, x - s):x + s + 1] = [b, b, b]

    return Image.fromarray(arr).filter(ImageFilter.GaussianBlur(0.4))


# ── Beach sunset ─────────────────────────────────────────────────────────────
def make_beach() -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    sky_h = int(H * 0.62)

    for y in range(sky_h):
        t = y / sky_h
        arr[y, :] = [
            int(20  + t * 235),   # R: dark blue → warm orange
            int(50  + t * 110),   # G
            int(180 - t * 145),   # B
        ]
    for y in range(sky_h, H):
        t = (y - sky_h) / (H - sky_h)
        arr[y, :] = [
            int(240 - t * 80),    # R: sandy warm
            int(170 - t * 90),    # G
            int(60  + t * 20),    # B
        ]

    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(3))

    # Sun disc
    draw = ImageDraw.Draw(img, "RGBA")
    sx, sy, sr = W // 2 + 60, sky_h - 80, 55
    draw.ellipse([(sx - sr, sy - sr), (sx + sr, sy + sr)], fill=(255, 220, 80, 220))

    return img.filter(ImageFilter.GaussianBlur(1))


# ── Forest ───────────────────────────────────────────────────────────────────
def make_forest() -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        t = y / H
        arr[y, :] = [int(15 + t * 25), int(55 + t * 75), int(15 + t * 20)]

    img = Image.fromarray(arr)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    rng = np.random.default_rng(7)
    for _ in range(14):
        x = int(rng.integers(0, W))
        y = int(rng.integers(0, int(H * 0.6)))
        r = int(rng.integers(50, 140))
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=(180, 230, 80, 35))

    overlay = overlay.filter(ImageFilter.GaussianBlur(30))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


# ── Studio white ─────────────────────────────────────────────────────────────
def make_studio_white() -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        t = y / H
        v = int(250 - t * 18)
        arr[y, :] = [v, v, v]
    return Image.fromarray(arr)


# ── Studio dark (charcoal) ───────────────────────────────────────────────────
def make_studio_dark() -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        t = y / H
        v = int(22 + t * 28)
        arr[y, :] = [v, v, v]
    return Image.fromarray(arr)


# ── Neon city ────────────────────────────────────────────────────────────────
def make_neon_city() -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        t = y / H
        arr[y, :] = [int(4 + t * 12), int(4 + t * 8), int(18 + t * 28)]

    img = Image.fromarray(arr)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    neon = [
        (255,  20, 147, 90),   # hot pink
        (  0, 200, 255, 80),   # cyan
        (160,  32, 240, 70),   # purple
        (  0, 255, 160, 70),   # mint
    ]
    for i, col in enumerate(neon):
        cy = int(H * (0.35 + i * 0.12))
        for dy in range(-35, 36):
            a = max(0, col[3] - abs(dy) * 2)
            draw.line([(0, cy + dy), (W, cy + dy)], fill=col[:3] + (a,))

    overlay = overlay.filter(ImageFilter.GaussianBlur(8))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB").filter(ImageFilter.GaussianBlur(1))


# ── Main ─────────────────────────────────────────────────────────────────────
print("Generating sample backgrounds …")
save("galaxy",       make_galaxy())
save("beach_sunset", make_beach())
save("forest",       make_forest())
save("studio_white", make_studio_white())
save("studio_dark",  make_studio_dark())
save("neon_city",    make_neon_city())
print("Done — 6 backgrounds written to", OUT)
