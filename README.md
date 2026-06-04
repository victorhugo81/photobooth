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
- **Event management** — create named events (e.g. "Smith Wedding"); photos are tagged to the active event; share a unique link so guests see only their event's photos
- **Decorative event themes** — 10 colour palettes for Christmas, Wedding, Halloween, etc.
- **Cloudflare R2 upload** — photos stored in the cloud with public share URLs
- **Local-only mode** — skip R2, store photos on device, serve them locally
- **Bulk upload** — one-click button to push all local photos to R2 when reconnecting
- **QR code** — shown after each capture and on the Live Show page; encodes the active event link so guests can scan and view the gallery
- **Live Show page** — full-screen 3×2 scrapbook grid, auto-cycles with new photos
- **Gallery page** — paginated scrapbook-style grid, automatically filtered to the active event
- **Photo detail page** — single photo view with download button
- **Admin panel** — all settings configurable from the browser, including `.env` editing

## Pages

| URL           | Description                                                      |
|---------------|------------------------------------------------------------------|
| `/`           | Main photobooth UI — preview, capture, background picker         |
| `/gallery`    | Paginated photo gallery (auto-filtered to active event)          |
| `/live-show`  | Full-screen slideshow for a second display                       |
| `/photo/<id>` | Single photo detail with download                                |
| `/admin`      | Settings panel                                                   |

Both `/gallery` and `/live-show` accept a `?event=evt_abc123` query parameter.
When an event is active the app redirects to include it automatically.

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

| Section                  | Description                                                              |
|--------------------------|--------------------------------------------------------------------------|
| **Events**               | Create named events; activate one to tag photos; copy share links        |
| **Event Type**           | Decorative colour theme and header emoji for gallery / live-show         |
| **Photo Label**          | Text stamped on every captured photo                                     |
| **Background Removal**   | Green Screen or AI Remove — applies to all captures                      |
| **QR Code URL**          | Base URL for the QR on the Live Show page (event param appended auto)    |
| **Online Access**        | Toggle cloud upload (R2) vs local-only storage                           |
| **Date Filter**          | Show only photos from a specific day (overridden by event filter)        |
| **UI Theme**             | Dark / White / Luxury / Black Rose colour scheme                         |
| **Upload Images**        | Add custom background images for background replacement                  |
| **Environment Config**   | Edit `.env` credentials directly from the browser                        |

## Event Management

Events let you run multiple separate photobooth sessions and give each group
their own private gallery link.

**Workflow:**

1. Go to **Admin → Events**, enter a name and date, click **+ Create**.
   The event is activated immediately — all photos taken while it is active
   are tagged to it.
2. Click **Copy Link** to get a shareable URL like:
   `http://192.168.1.x:5000/live-show?event=evt_abc123`
3. Send that link to guests. They see only photos from their event — no photos
   from other sessions are visible.
4. When the event is over, click **Stop** to deactivate, or create a new event
   (which activates automatically and deactivates the previous one).

**QR code behaviour:**

- When an event is active the QR on the Live Show page and the QR shown after
  each capture both encode the event link.
- If no **QR Code URL** base is configured in admin, the QR auto-generates
  using the Pi's own address (`http://<host>/live-show?event=evt_abc123`).

## Photo Storage

### Cloud mode (Online Access: Yes)
Photos are uploaded to a Cloudflare R2 bucket under `YYYY-MM-DD/photo_*.jpg`.
When an event is active the post-capture QR encodes the event link. When no event
is active, a per-photo share QR is generated pointing at `SHARE_SITE_URL/?f=<key>`.

### Local mode (Online Access: No)
Photos are saved to `templates/photos/YYYY-MM-DD/` and served by the app at
`/photos/<date>/<filename>`. Use the **Upload Local Photos to Cloud** button in
admin to bulk-push them to R2 later.

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
- Event records are stored in `templates/data/events.json` (synced to R2).
  Photo-to-event associations are stored in SQLite (`event_id` column on the
  `photos` table).
