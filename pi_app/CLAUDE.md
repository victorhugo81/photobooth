# pi_app — Raspberry Pi Photobooth Controller

Flask app that runs on a Raspberry Pi. Controls the camera, uploads photos to
Cloudflare R2, generates a QR code, and displays a live MJPEG preview.

## Tech Stack

| Layer      | Library                          |
|------------|----------------------------------|
| Web        | Flask 3                          |
| Camera     | picamera2 (Pi) / cv2 fallback    |
| Upload     | boto3 (Cloudflare R2, S3 API)    |
| QR code    | qrcode[pil]                      |
| Preview    | opencv-python (MJPEG stream)     |
| Database   | SQLAlchemy 2 + SQLite            |
| GPIO       | gpiozero (optional, pin 17)      |
| Config     | python-dotenv                    |
| Packaging  | uv                               |

## Routes

| Method | Path          | Description                                              |
|--------|---------------|----------------------------------------------------------|
| GET    | `/`           | Main UI — live preview + capture button                  |
| GET    | `/video_feed` | MJPEG stream (multipart/x-mixed-replace)                 |
| POST   | `/capture`    | Trigger countdown → capture → upload → QR; returns JSON  |
| GET    | `/status`     | JSON of the last capture result                          |

## Environment Variables (copy `.env.example` → `.env`)

| Variable              | Description                                          |
|-----------------------|------------------------------------------------------|
| `R2_ACCOUNT_ID`       | Cloudflare account ID (from R2 dashboard)            |
| `R2_ACCESS_KEY_ID`    | R2 API token access key                              |
| `R2_SECRET_ACCESS_KEY`| R2 API token secret                                  |
| `R2_BUCKET_NAME`      | R2 bucket name                                       |
| `R2_PUBLIC_URL`       | Public base URL of bucket (no trailing slash)        |
| `SHARE_SITE_URL`      | URL of the deployed share_site (no trailing slash)   |

## Installation & Run

### Development (non-Pi, uses USB webcam or test pattern)

```bash
cd pi_app
uv sync
cp .env.example .env   # fill in real values
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

### Raspberry Pi (includes camera + GPIO)

```bash
cd pi_app
uv sync --extra pi
cp .env.example .env
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

For a kiosk / autostart, run via systemd or a simple shell script with gunicorn:

```bash
uv run gunicorn "app:create_app()" --bind 0.0.0.0:5000 --workers 1 --threads 4
```

## Camera Fallback Tiers

1. **picamera2** — Pi camera module (production, requires `--extra pi`)
2. **cv2.VideoCapture(0)** — USB webcam or laptop camera (development)
3. **Synthetic test pattern** — rendered by Pillow (no hardware, CI)

## File Layout

```
pi_app/
├── app.py            Flask app factory + routes
├── camera.py         Camera class + mjpeg_generator()
├── uploader.py       Cloudflare R2 upload via boto3
├── qr_generator.py   QR PNG generation via qrcode[pil]
├── models.py         SQLAlchemy Photo model + init_db()
├── templates/
│   └── index.html    Bootstrap 5 UI
├── static/
│   └── qr_codes/     Generated QR PNGs (gitignored)
├── photos/           Captured JPEGs (gitignored)
├── .env.example
└── pyproject.toml
```
