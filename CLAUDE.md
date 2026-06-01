# pi_app — Raspberry Pi Photobooth Controller

Flask app that runs on a Raspberry Pi. Controls the camera, applies photo frame
themes, uploads photos to Cloudflare R2, generates a QR code, and displays a
live MJPEG preview. Includes a full admin UI, a paginated gallery, and a
full-screen live-show display page.

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

### Pages

| Method | Path          | Description                                                        |
|--------|---------------|--------------------------------------------------------------------|
| GET    | `/`           | Main UI — live preview, background picker, capture button          |
| GET    | `/admin`      | Settings — event type, photo label, QR URL, UI theme, backgrounds |
| GET    | `/gallery`    | Paginated photo gallery (12 per page, scrapbook card style)        |
| GET    | `/live-show`  | Full-screen live display — 6 dynamic slots, cycling slideshow      |

### API

| Method | Path                    | Description                                              |
|--------|-------------------------|----------------------------------------------------------|
| GET    | `/video_feed`           | MJPEG stream (multipart/x-mixed-replace)                 |
| POST   | `/capture`              | Trigger capture → theme → upload → QR; returns JSON      |
| GET    | `/themes`               | JSON list of available photo frame themes                |
| GET    | `/backgrounds`          | JSON list of uploaded background images                  |
| POST   | `/backgrounds/upload`   | Upload a new background image                            |
| DELETE | `/backgrounds/<id>`     | Delete a background image                                |
| GET    | `/backgrounds/<id>/color` | Dominant colour of a background                        |
| GET    | `/api/photos`           | JSON array of all photos, newest first                   |
| GET    | `/api/event`            | Get current event type                                   |
| POST   | `/api/event`            | Set event type                                           |
| GET    | `/api/label`            | Get photo label text                                     |
| POST   | `/api/label`            | Set photo label text                                     |
| GET    | `/api/qr-url`           | Get QR code URL                                          |
| POST   | `/api/qr-url`           | Set QR code URL                                          |
| GET    | `/api/ui-theme`         | Get active UI theme                                      |
| POST   | `/api/ui-theme`         | Set UI theme                                             |
| GET    | `/api/date-filter`      | Get active date filter (`{"date":"YYYY-MM-DD"}` or null) |
| POST   | `/api/date-filter`      | Set date filter (`{"date":"YYYY-MM-DD"}` or `null`)      |
| GET    | `/qr-image`             | Serve QR code as PNG (generated in memory)               |
| GET    | `/status`               | JSON of the last capture result                          |
| GET    | `/capabilities`         | JSON of available features (e.g. rembg)                  |

`/capture` accepts JSON body: `{ "theme": "classic", "background": "none", "removal": "greenscreen" }`.

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

| ID         | Name      | Effect                                                      |
|------------|-----------|-------------------------------------------------------------|
| `none`     | Original  | No modification                                             |
| `classic`  | Classic   | White polaroid border (wider at bottom, "PHOTOBOOTH" label) |
| `birthday` | Birthday  | Rainbow stripe border (coral, yellow, green, blue, pink)    |
| `vintage`  | Vintage   | Sepia + reduced contrast + warm brown border                |

To add a new frame theme: add a function in `themes.py`, register it in `THEMES`,
then add a matching button + CSS class in `templates/index.html`.

## Event Types

Selected in admin. Controls the gallery/live-show background pattern and colour
palette (`gallery.css` `body.event-*` overrides) and the header emoji icon.

| Key              | Label          |
|------------------|----------------|
| `default`        | Default        |
| `christmas`      | Christmas      |
| `birthday`       | Birthday       |
| `graduation`     | Graduation     |
| `wedding`        | Wedding        |
| `girls_birthday` | Girl's Birthday|
| `boys_birthday`  | Boy's Birthday |
| `new_years`      | New Year's     |
| `halloween`      | Halloween      |
| `fourth_of_july` | 4th of July    |

To add a new event: add the key to `_VALID_EVENTS` in `app.py`, add a
`body.event-<key>` block in `gallery.css`, add an icon entry in both
`gallery.html` and `live-show.html`, and add a button + swatch in
`admin.html` / `admin.css`.

## UI Themes

Selected in admin. Controls the overall colour palette for admin, gallery,
and live-show pages via CSS custom properties in `main.css`.

| Key          | Description                  |
|--------------|------------------------------|
| `dark`       | Dark grey (default)          |
| `white`      | Clean white                  |
| `luxury`     | Black with gold accents      |
| `black-rose` | Dark with rose-pink accents  |

To add a new UI theme: add a `body.theme-<key>` block in `main.css`, add the
key to `_VALID_UI_THEMES` in `app.py`, and add a button + swatch in
`admin.html` / `admin.css`.

## Settings Persistence (data files)

All settings are stored as JSON in `templates/data/` and synced to
`data/<filename>` in the R2 bucket on every save. On startup, the app
restores all data files from R2 so settings survive Pi reboots and redeployments.

| File            | Contents                        |
|-----------------|---------------------------------|
| `event.json`       | `{ "event": "default" }`                     |
| `label.json`       | `{ "text": "PHOTOBOOTH" }`                   |
| `ui_theme.json`    | `{ "theme": "dark" }`                        |
| `qr_url.json`      | `{ "url": "" }`                              |
| `date_filter.json` | `{ "date": "YYYY-MM-DD" }` or `{"date": null}` |
| `photos.json`      | `["YYYY-MM-DD/photo_….jpg", …]` (newest first) |

## R2 Storage Layout

```
<bucket>/
├── data/
│   ├── event.json
│   ├── label.json
│   ├── ui_theme.json
│   ├── qr_url.json
│   └── photos.json          Flat JSON array of keys ("YYYY-MM-DD/photo_….jpg"), newest first
└── YYYY-MM-DD/
    └── photo_YYYYMMDD_HHMMSS.jpg  Captured photos organised by capture date
```

Photos are stored under a `YYYY-MM-DD/` prefix matching their UTC capture date.
`photos.json` entries and the SQLite `filename` column store the full key
(e.g. `2024-06-01/photo_20240601_143022.jpg`). The `r2_url` and `share_url`
`?f=` parameter both include the date prefix.

## Live Show Page (`/live-show`)

Full-screen 3×2 grid of photo cards with scrapbook styling (polaroid border,
tape strip, random tilt). Powered by `gallery.js`.

- **Slot 0** (top-left): always shows the most recent photo. Polls every 3 s
  and updates with a 1.2 s fade only when a new capture is detected.
- **Slots 1–5**: cycle through all photos in batches of 5, advancing every 15 s
  with a fade transition.
- **QR code overlay**: shown when a QR URL is configured in admin. Fixed to the
  bottom-right corner on large screens (≥ 768 px); flows below the grid on
  small screens so users can scroll to it.

## File Layout

```
pi_app/
├── app.py              Flask app factory + routes + GPIO listener
├── camera.py           Camera class + mjpeg_generator()
├── themes.py           Pillow frame compositing
├── uploader.py         R2 upload, photos.json update, data file sync
├── qr_generator.py     QR PNG generation (file and in-memory)
├── models.py           SQLAlchemy Photo model + init_db()
├── backgrounds.py      Background image management
├── templates/
│   ├── index.html      Main photobooth UI
│   ├── admin.html      Settings page
│   ├── gallery.html    Paginated photo gallery
│   ├── live-show.html  Full-screen live display
│   └── data/           Persisted settings JSON files
├── static/
│   ├── css/
│   │   ├── main.css        Shared variables + header styles + UI themes
│   │   ├── index.css       Photobooth main page styles
│   │   ├── admin.css       Admin page styles
│   │   ├── gallery.css     Gallery styles + event theme overrides
│   │   └── live-show.css   Full-screen layout + QR overlay
│   ├── js/
│   │   ├── index.js        Capture flow, background picker, countdown
│   │   ├── admin.js        Settings save/load, background upload
│   │   └── gallery.js      Live-show polling + slideshow logic
│   └── qr_codes/           Generated QR PNGs (gitignored)
├── photos/             Captured JPEGs (gitignored)
├── .env.example
└── pyproject.toml
```
