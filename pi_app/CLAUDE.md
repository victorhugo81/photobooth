# pi_app — Raspberry Pi Photobooth Controller

Flask app that runs on a Raspberry Pi. Controls the camera, applies photo frame
themes, uploads photos to Cloudflare R2, generates a QR code, and displays a
live MJPEG preview.

## Tech Stack

| Layer      | Library                                 |
|------------|-----------------------------------------|
| Web        | Flask 3                                 |
| Camera     | picamera2 (Pi, via apt) / cv2 fallback  |
| Upload     | boto3 (Cloudflare R2, S3-compatible)    |
| QR code    | qrcode[pil]                             |
| Streaming  | opencv-python-headless (MJPEG frames)   |
| Themes     | Pillow compositing                      |
| Database   | SQLAlchemy 2 + SQLite                   |
| GPIO       | gpiozero (optional, pin 17, via apt)    |
| Config     | python-dotenv                           |
| Packaging  | uv (`package = false`)                  |

## Routes

| Method | Path          | Description                                               |
|--------|---------------|-----------------------------------------------------------|
| GET    | `/`           | Main UI — live preview, theme picker, capture button      |
| GET    | `/video_feed` | MJPEG stream (multipart/x-mixed-replace)                  |
| POST   | `/capture`    | Trigger countdown → capture → theme → upload → QR; JSON   |
| GET    | `/themes`     | JSON list of available themes with id, name, preview      |
| GET    | `/status`     | JSON of the last capture result                           |

`/capture` accepts JSON body: `{ "theme": "classic" }` (default `"none"`).

## Environment Variables (copy `.env.example` → `.env`)

| Variable               | Description                                          |
|------------------------|------------------------------------------------------|
| `R2_ACCOUNT_ID`        | Cloudflare account ID (from R2 dashboard)            |
| `R2_ACCESS_KEY_ID`     | R2 API token access key                              |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret                                  |
| `R2_BUCKET_NAME`       | R2 bucket name                                       |
| `R2_PUBLIC_URL`        | Public base URL of bucket (no trailing slash)        |
| `SHARE_SITE_URL`       | URL of the deployed share_site (no trailing slash)   |

## Installation & Run

### Development (non-Pi, uses USB webcam or test pattern)

```bash
cd pi_app
uv sync
cp .env.example .env   # fill in real values
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

### Raspberry Pi

picamera2 and gpiozero are **not** in pyproject.toml (they can only build on
Linux with system libraries). Install them via apt before running:

```bash
sudo apt install python3-picamera2 python3-gpiozero
cd pi_app
uv sync
cp .env.example .env
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

For a kiosk / autostart, use gunicorn:

```bash
uv run gunicorn "app:create_app()" --bind 0.0.0.0:5000 --workers 1 --threads 4
```

## Camera Fallback Tiers

1. **picamera2** — Pi camera module; stills use `switch_mode_and_capture_file`
   with `create_still_configuration()` for full-sensor resolution
2. **cv2.VideoCapture(0)** — USB webcam or laptop camera (development)
3. **Synthetic test pattern** — rendered by Pillow (no hardware, CI)

## Photo Frame Themes

Themes are applied **after** capture and **before** R2 upload via Pillow compositing
in `themes.py`. The UI shows a live CSS preview of the selected theme on the video wrapper.

| ID         | Name      | Effect                                                    |
|------------|-----------|-----------------------------------------------------------|
| `none`     | Original  | No modification                                           |
| `classic`  | Classic   | White polaroid border (wider at bottom, "PHOTOBOOTH" label) |
| `birthday` | Birthday  | Rainbow stripe border (coral, yellow, green, blue, pink)  |
| `vintage`  | Vintage   | Sepia + reduced contrast + warm brown border              |

To add a new theme: add a function in `themes.py` and register it in `THEMES`,
then add a matching button + CSS class in `templates/index.html`.

## R2 Storage Layout

```
<bucket>/
├── photos.json          Flat JSON array of filenames, newest first
├── photo_YYYYMMDD_HHMMSS.jpg  Captured photos (with theme applied)
└── ...
```

`photos.json` is updated on every capture. Format: `["photo_20260529_183704.jpg", ...]`

## File Layout

```
pi_app/
├── app.py            Flask app factory + routes + GPIO listener
├── camera.py         Camera class + mjpeg_generator()
├── themes.py         Pillow frame compositing (4 themes)
├── uploader.py       Cloudflare R2 upload + photos.json update
├── qr_generator.py   QR PNG generation via qrcode[pil]
├── models.py         SQLAlchemy Photo model + init_db()
├── templates/
│   └── index.html    Bootstrap 5 dark UI (theme picker + live preview)
├── static/
│   └── qr_codes/     Generated QR PNGs (gitignored)
├── photos/           Captured JPEGs (gitignored)
├── .env.example
└── pyproject.toml
```
