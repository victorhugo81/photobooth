# Raspberry Pi Photobooth

Flask app that runs on a Raspberry Pi (or any machine for development). Controls
the camera, applies photo frame themes, optionally uploads photos to Cloudflare R2,
generates a QR code, and displays a live MJPEG preview. Includes a full admin UI,
a paginated gallery, a single-photo detail page, and a full-screen live-show display.

## Tech Stack

| Layer      | Library                                 |
|------------|-----------------------------------------|
| Web        | Flask 3                                 |
| Camera     | picamera2 (Pi, via apt) / cv2 fallback  |
| Upload     | boto3 (Cloudflare R2, S3-compatible)    |
| QR code    | qrcode[pil]                             |
| Streaming  | opencv-python-headless (MJPEG frames)   |
| Themes     | Pillow compositing                      |
| BG removal | rembg (U2Net AI) / OpenCV HSV chroma-key|
| Database   | SQLAlchemy 2 + SQLite                   |
| GPIO       | gpiozero (optional, pin 17, via apt)    |
| Config     | python-dotenv                           |
| Packaging  | uv (`package = false`)                  |

## Routes

### Pages

| Method | Path                    | Description                                                         |
|--------|-------------------------|---------------------------------------------------------------------|
| GET    | `/`                     | Main UI — live preview, background picker, capture button           |
| GET    | `/admin`                | Settings — events, label, removal mode, QR URL, online access, theme|
| GET    | `/gallery`              | Paginated photo gallery (12 per page); auto-redirects to active event|
| GET    | `/live-show`            | Full-screen live display — 6 dynamic slots; auto-redirects to active event|
| GET    | `/photo/<path:filename>`| Single-photo detail page with download button                       |

Both `/gallery` and `/live-show` accept `?event=evt_abc123` and `?date=YYYY-MM-DD`
query parameters. When an event is active and no filter is in the URL, both routes
redirect automatically to include `?event=<active-id>`.

### API

| Method | Path                            | Description                                                      |
|--------|---------------------------------|------------------------------------------------------------------|
| GET    | `/video_feed`                   | MJPEG stream (multipart/x-mixed-replace)                         |
| POST   | `/capture`                      | Trigger capture → theme → upload → QR; returns JSON              |
| GET    | `/themes`                       | JSON list of available photo frame themes                        |
| GET    | `/backgrounds`                  | JSON list of uploaded background images                          |
| POST   | `/backgrounds/upload`           | Upload a new background image                                    |
| DELETE | `/backgrounds/<id>`             | Delete a background image                                        |
| GET    | `/backgrounds/<id>/color`       | Dominant colour of a background                                  |
| GET    | `/photos/<path:filename>`       | Serve a locally-stored photo (used when online access is off)    |
| GET    | `/api/photos`                   | JSON array of photos; accepts `?event=` or `?date=` filter       |
| GET    | `/api/events`                   | List all event records                                           |
| POST   | `/api/events`                   | Create event `{name, date}` — activates immediately              |
| POST   | `/api/events/<id>/activate`     | Set event as active (deactivates all others)                     |
| POST   | `/api/events/deactivate`        | Deactivate all events (no active event)                          |
| DELETE | `/api/events/<id>`              | Delete event (must be inactive first)                            |
| GET    | `/api/event`                    | Get current decorative event type                                |
| POST   | `/api/event`                    | Set decorative event type                                        |
| GET    | `/api/label`                    | Get photo label text                                             |
| POST   | `/api/label`                    | Set photo label text                                             |
| GET    | `/api/qr-url`                   | Get QR code base URL                                             |
| POST   | `/api/qr-url`                   | Set QR code base URL                                             |
| GET    | `/api/ui-theme`                 | Get active UI theme                                              |
| POST   | `/api/ui-theme`                 | Set UI theme                                                     |
| GET    | `/api/date-filter`              | Get active date filter (`{"date":"YYYY-MM-DD"}` or null)         |
| POST   | `/api/date-filter`              | Set date filter (`{"date":"YYYY-MM-DD"}` or `null`)              |
| GET    | `/api/online-access`            | Get online access setting + R2 config status                     |
| POST   | `/api/online-access`            | Enable/disable cloud upload (`{"enabled": true/false}`)          |
| POST   | `/api/bulk-upload`              | Upload all local photos to R2                                    |
| GET    | `/api/removal-mode`             | Get background removal mode + rembg availability                 |
| POST   | `/api/removal-mode`             | Set removal mode (`{"mode": "greenscreen" \| "ai"}`)             |
| GET    | `/api/env`                      | Read current `.env` values (all editable keys)                   |
| POST   | `/api/env`                      | Write key/value pairs to `.env` and reload                       |
| GET    | `/qr-image`                     | Serve QR code as PNG; encodes event link when event is active    |
| GET    | `/status`                       | JSON of the last capture result                                  |
| GET    | `/capabilities`                 | JSON of available features (`{"rembg": true/false}`)             |

`/capture` accepts JSON body: `{ "theme": "classic", "background": "none" }`.
Removal mode is read server-side from `removal_mode.json` — not sent by the client.

`/api/photos` filter priority: `?event=` > `?date=` > server-side date filter.

## Environment Variables

Stored in `.env` at the repo root. Editable via the admin page's Environment
Configuration section without restarting — changes to R2/share-site credentials
require a restart to fully take effect.

| Variable               | Description                                          |
|------------------------|------------------------------------------------------|
| `R2_ACCOUNT_ID`        | Cloudflare account ID (from R2 dashboard)            |
| `R2_ACCESS_KEY_ID`     | R2 API token access key                              |
| `R2_SECRET_ACCESS_KEY` | R2 API token secret                                  |
| `R2_BUCKET_NAME`       | R2 bucket name                                       |
| `R2_PUBLIC_URL`        | Public base URL of bucket (no trailing slash)        |
| `SHARE_SITE_URL`       | URL of the deployed share site (no trailing slash)   |
| `PHOTOSLIDE_URL`       | Optional gallery link shown in the header            |
| `FLASK_ENV`            | `production` or `development`                        |
| `FLASK_RUN_HOST`       | Bind address (default `0.0.0.0`)                     |
| `FLASK_RUN_PORT`       | Port (default `5000`)                                |

All R2 variables are optional — if `R2_ACCOUNT_ID` is missing the app runs in
local-only mode automatically.

## Installation & Run

### Development (Windows / Mac / Linux — uses webcam or test pattern)

```bash
uv sync
cp .env.example .env   # fill in real values, or leave R2 vars empty for local-only
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

### Raspberry Pi

picamera2 and gpiozero are **not** in pyproject.toml (system libraries only).
Install them via apt before running:

```bash
sudo apt install python3-picamera2 python3-gpiozero
uv sync
# Expose apt-installed packages to the uv venv (one-time; survives uv sync):
echo "/usr/lib/python3/dist-packages" > .venv/lib/python3.13/site-packages/system-dist-packages.pth
cp .env.example .env
uv run flask --app app:create_app run --host 0.0.0.0 --port 5000
```

> **Why the `.pth` file?** uv isolates its venv from system site-packages.
> On Raspberry Pi OS, apt packages land in `/usr/lib/python3/dist-packages`
> (not the standard `site-packages`), so even `--system-site-packages` doesn't
> expose them. The `.pth` file adds that path permanently without being removed
> by `uv sync`.

For kiosk / autostart use gunicorn:

```bash
uv run gunicorn "app:create_app()" --bind 0.0.0.0:5000 --workers 1 --threads 4
```

## Camera Fallback Tiers

1. **picamera2** — Pi camera module; stills via `switch_mode_and_capture_file`.
   Preview frames are captured as `RGB888` (which picamera2 stores as BGR in
   memory) and flipped to RGB before being handed to Pillow.
2. **cv2.VideoCapture(0)** — USB webcam or laptop camera (development)
3. **Synthetic test pattern** — rendered by Pillow (no hardware / CI)

## Event Management

Events associate photos with a named session and generate a private gallery link.

- Events are stored in `templates/data/events.json` (array, newest first), synced to R2.
- Only one event can be active at a time. Creating a new event deactivates the previous one.
- Every photo captured while an event is active has its `event_id` stored in SQLite.
- The share link for an event is `http://<host>/live-show?event=<id>`. Guests who open
  that link see only photos tagged to that event — no cross-event leakage.
- The post-capture QR and the live-show QR both encode the event link when an event is active.
- If no QR URL base is configured in admin, `/qr-image` auto-uses `{request.url_root}live-show`.

## Online Access & Storage

Toggled in admin under **Online Access**.

- **Yes (enabled):** photos uploaded to R2 after capture; `photos.json` updated.
  QR target priority: event link (if active + QR URL set) > per-photo share URL > date link.
  If the upload fails, the photo is saved locally and the result includes `upload_error`.
- **No (disabled):** photos saved only to `templates/photos/YYYY-MM-DD/`; served
  locally via `/photos/<path>`. Use the **Upload Local Photos to Cloud** button in
  admin to bulk-push them to R2 later (`POST /api/bulk-upload`).

## Background Removal

Set in admin under **Background Removal** (applies to all captures).

| Mode          | How it works                                           |
|---------------|--------------------------------------------------------|
| `greenscreen` | OpenCV HSV chroma-key — requires a physical green screen |
| `ai`          | rembg U2Net model — works on any background, slower   |

If `ai` is selected but rembg is unavailable, the app falls back to `greenscreen`
automatically at capture time.

## Photo Frame Themes

Applied after capture, before upload, via Pillow compositing in `themes.py`.

| ID         | Name      | Effect                                                      |
|------------|-----------|-------------------------------------------------------------|
| `none`     | Original  | No modification                                             |
| `classic`  | Classic   | White polaroid border (wider at bottom, label + date)       |
| `birthday` | Birthday  | Rainbow stripe border                                       |
| `vintage`  | Vintage   | Sepia + reduced contrast + warm brown border                |

To add a theme: add a function in `themes.py`, register in `THEMES`, add button +
CSS in `templates/index.html`.

## Decorative Event Types

Selected in admin under **Event Type**. Controls gallery/live-show background
pattern, colour palette (`gallery.css` `body.event-*` overrides), and header emoji.
Separate from event records — this is purely cosmetic.

| Key              | Label           |
|------------------|-----------------|
| `default`        | Default         |
| `christmas`      | Christmas       |
| `birthday`       | Birthday        |
| `graduation`     | Graduation      |
| `wedding`        | Wedding         |
| `girls_birthday` | Girl's Birthday |
| `boys_birthday`  | Boy's Birthday  |
| `new_years`      | New Year's      |
| `halloween`      | Halloween       |
| `fourth_of_july` | 4th of July     |

To add: add key to `_VALID_EVENTS` in `app.py`, add `body.event-<key>` block in
`gallery.css`, add icon in `gallery.html` + `live-show.html`, add button + swatch
in `admin.html` / `admin.css`.

## UI Themes

Selected in admin. Controls colour palette via CSS custom properties in `main.css`.

| Key          | Description                 |
|--------------|-----------------------------|
| `dark`       | Dark grey (default)         |
| `white`      | Clean white                 |
| `luxury`     | Black with gold accents     |
| `black-rose` | Dark with rose-pink accents |

To add a theme: add `body.theme-<key>` block in `main.css`, add key to
`_VALID_UI_THEMES` in `app.py`, add button + swatch in `admin.html` / `admin.css`.

## Settings Persistence (data files)

All settings stored as JSON in `templates/data/` and synced to `data/<filename>`
in R2 on every save. On startup the app restores all files from R2 so settings
survive Pi reboots.

| File                  | Contents                                                        |
|-----------------------|-----------------------------------------------------------------|
| `events.json`         | `[{id, name, date, active, created_at}, …]` (newest first)     |
| `event.json`          | `{ "event": "default" }` — decorative event type               |
| `label.json`          | `{ "text": "PHOTOBOOTH" }`                                      |
| `ui_theme.json`       | `{ "theme": "dark" }`                                           |
| `qr_url.json`         | `{ "url": "" }` — QR base URL                                   |
| `date_filter.json`    | `{ "date": "YYYY-MM-DD" }` or `{ "date": null }`                |
| `online_access.json`  | `{ "enabled": true }`                                           |
| `removal_mode.json`   | `{ "mode": "greenscreen" }`                                     |
| `photos.json`         | `["YYYY-MM-DD/photo_….jpg", …]` (newest first)                  |

## R2 Storage Layout

```
<bucket>/
├── data/
│   ├── events.json
│   ├── event.json
│   ├── label.json
│   ├── ui_theme.json
│   ├── qr_url.json
│   ├── date_filter.json
│   ├── online_access.json
│   ├── removal_mode.json
│   ├── photos.json
│   └── qr_codes/
│       └── qr_event_<id>.png   ← one per event
└── YYYY-MM-DD/
    └── photo_YYYYMMDD_HHMMSS.jpg
```

`photos.json` entries and the SQLite `filename` column store the full key
(e.g. `2024-06-01/photo_20240601_143022.jpg`).

## Live Show Page (`/live-show`)

Full-screen 3×2 grid (desktop) / 2×3 (tablet/mobile). Grid is sized to fit
exactly within the viewport — no scrolling. Powered by `gallery.js`.

- **Slot 0** (top-left): always the most recent photo. Polls every 3 s, updates
  with a 1.2 s fade on new capture.
- **Slots 1–5**: cycle through all photos in batches of 5, advancing every 15 s.
- **QR code**: fixed bottom-right on large screens (≥ 768 px); fixed
  bottom-centre on mobile with padding reserved so the grid isn't hidden behind it.
- **Event filter**: `?event=evt_abc123` in the URL restricts all photos to that event.
  `gallery.js` reads `URL_EVENT` from `window.location.search` and passes it to
  `/api/photos?event=`. When an active event exists the route auto-redirects.

## Admin Page (`/admin`)

Settings sections in order:

1. **Events** — create named events, activate/stop, copy share links
2. **Event Type** — decorative gallery/live-show colour theme and emoji
3. **Photo Label** — text stamped on captured photos
4. **Background Removal** — Green Screen or AI Remove (persisted, applies to all captures)
5. **QR Code URL** — base URL appended with `?event=<id>` (or `?date=`) for the live-show QR
6. **Online Access** — Yes (upload to R2) or No (local only); bulk-upload button when R2 configured
7. **Date Filter** — restrict gallery + live-show to a specific day (overridden by event filter)
8. **UI Theme** — Dark / White / Luxury / Black Rose
9. **Upload Images** — upload custom background images
10. **Environment Configuration** — edit `.env` file from the browser

## File Layout

```
photobooth/               ← repo root
├── app.py                Flask app factory + routes + GPIO listener
├── camera.py             Camera class + mjpeg_generator()
├── themes.py             Pillow frame compositing
├── uploader.py           R2 upload, photos.json update, data file sync
├── qr_generator.py       QR PNG generation (file and in-memory)
├── models.py             SQLAlchemy Photo model (+ event_id column) + init_db()
├── backgrounds.py        Background image management + rembg wrapper
├── pyproject.toml        uv project — dependencies
├── .env                  Runtime secrets (gitignored)
├── photobooth.db         SQLite database (gitignored)
├── templates/
│   ├── index.html        Main photobooth UI
│   ├── admin.html        Settings page
│   ├── gallery.html      Paginated photo gallery
│   ├── live-show.html    Full-screen live display
│   ├── photo.html        Single-photo detail view
│   └── data/             Persisted settings JSON files (incl. events.json)
├── static/
│   ├── css/
│   │   ├── main.css          Shared variables + header + UI themes
│   │   ├── index.css         Main photobooth page styles
│   │   ├── admin.css         Admin page styles (incl. event record rows)
│   │   ├── gallery.css       Gallery styles + event theme overrides
│   │   └── live-show.css     Full-screen layout + QR overlay
│   ├── js/
│   │   ├── index.js          Capture flow, background picker, countdown
│   │   ├── admin.js          Settings save/load, event management, background upload
│   │   └── gallery.js        Live-show polling + slideshow logic (reads ?event= / ?date=)
│   ├── backgrounds/          Uploaded background images
│   └── qr_codes/             Generated QR PNGs (gitignored)
└── photos/                   Captured JPEGs (gitignored, local-only mode)
```
