# Raspberry Pi Photobooth

A self-hosted photobooth built with Flask. Runs on a Raspberry Pi with a camera
module, or on any laptop/desktop using a webcam for development. Captures photos,
applies vintage frame themes, optionally uploads to Cloudflare R2, and displays
a real-time live show on a second screen.

## Features

- **Live MJPEG preview** — full-resolution camera feed in the browser
- **Countdown + capture** — 3-second countdown, then photo taken
- **Background replacement** — Green Screen (chroma-key) or AI Remove (rembg)
- **Photo frame themes** — Classic polaroid, Birthday, Vintage
- **Event themes** — 10 colour palettes for Christmas, Wedding, Halloween, etc.
- **Cloudflare R2 upload** — photos stored in the cloud with public share URLs
- **Local-only mode** — skip R2, store photos on device, serve them locally
- **QR code** — generated after each capture; points to the share page or a custom URL
- **Live Show page** — full-screen 3×2 scrapbook grid, auto-cycles with new photos
- **Gallery page** — paginated scrapbook-style grid with date filtering
- **Photo detail page** — single photo view with download button
- **Admin panel** — all settings configurable from the browser, including `.env` editing

## Pages

| URL           | Description                                             |
|---------------|---------------------------------------------------------|
| `/`           | Main photobooth UI — preview, capture, background picker|
| `/gallery`    | Paginated photo gallery with date filter                |
| `/live-show`  | Full-screen slideshow for a second display              |
| `/photo/<id>` | Single photo detail with download                       |
| `/admin`      | Settings panel                                          |

## Quick Start

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Webcam (development) or Raspberry Pi camera module (Pi)

### Run locally (development)

```bash
git clone <repo-url>
cd photobooth
uv sync
cp .env.example .env        # optional — leave R2 vars empty for local-only mode
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

Open `http://localhost:5000` in your browser.

### Run on Raspberry Pi

```bash
sudo apt install python3-picamera2 python3-gpiozero
uv sync
cp .env.example .env
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

For kiosk / autostart:

```bash
uv run gunicorn "app:create_app()" --bind 0.0.0.0:5000 --workers 1 --threads 4
```

## Configuration

All settings can be changed live from the **Admin** page at `/admin`.
For R2 credentials and server settings, use the **Environment Configuration**
section at the bottom of the admin page — changes are written to `.env` directly
from the browser.

### Environment Variables

| Variable               | Required | Description                                   |
|------------------------|----------|-----------------------------------------------|
| `R2_ACCOUNT_ID`        | No       | Cloudflare account ID                         |
| `R2_ACCESS_KEY_ID`     | No       | R2 API token access key                       |
| `R2_SECRET_ACCESS_KEY` | No       | R2 API token secret                           |
| `R2_BUCKET_NAME`       | No       | R2 bucket name                                |
| `R2_PUBLIC_URL`        | No       | Public URL of bucket (no trailing slash)      |
| `SHARE_SITE_URL`       | No       | URL of the share site (no trailing slash)     |
| `PHOTOSLIDE_URL`       | No       | Optional gallery link in the header           |

All R2 variables are optional. When omitted the app runs in **local-only mode**
automatically — photos are saved to disk and served from `/photos/<path>`.

## Admin Settings

| Section                  | Description                                                   |
|--------------------------|---------------------------------------------------------------|
| **Event Type**           | Sets the gallery/live-show colour theme and header emoji      |
| **Photo Label**          | Text stamped on every captured photo                          |
| **Background Removal**   | Green Screen or AI Remove — applies to all captures           |
| **QR Code URL**          | URL shown as a QR code on the Live Show page                  |
| **Online Access**        | Toggle cloud upload (R2) vs local-only storage                |
| **Date Filter**          | Show only photos from a specific day in gallery + live show   |
| **UI Theme**             | Dark / White / Luxury / Black Rose colour scheme              |
| **Upload Images**        | Add custom background images for background replacement       |
| **Environment Config**   | Edit `.env` credentials directly from the browser             |

## Photo Storage

### Cloud mode (Online Access: Yes)
Photos are uploaded to a Cloudflare R2 bucket under `YYYY-MM-DD/photo_*.jpg`.
A per-photo share QR is generated pointing at `SHARE_SITE_URL/?f=<key>`.

### Local mode (Online Access: No)
Photos are saved to `templates/photos/YYYY-MM-DD/` and served by the app at
`/photos/<date>/<filename>`. The QR after capture encodes the **QR Code URL**
set in admin (e.g. your gallery address).

## Camera Fallback

1. **picamera2** — Raspberry Pi camera module
2. **cv2.VideoCapture(0)** — USB webcam or laptop camera
3. **Synthetic test pattern** — Pillow-generated image (no hardware needed)

The correct tier is selected automatically at startup.

## Physical Button (Pi)

Connect a momentary push button to **GPIO pin 17** (and GND). The app detects
`gpiozero` at startup and registers a capture trigger — same as pressing the
on-screen button.

## Development Notes

- `uv sync` installs all Python dependencies into `.venv/`
- `rembg` (AI background removal) is included in `pyproject.toml` and installs on
  all platforms. If the model weights aren't downloaded yet, the first AI capture
  will be slow while rembg fetches them.
- `picamera2` and `gpiozero` are **system packages** — install via `apt` on Pi,
  not via `uv`.
- Settings survive reboots: on startup the app pulls all `templates/data/*.json`
  files from R2 (when configured) so admin settings persist across redeployments.
