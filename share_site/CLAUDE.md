# share_site — Photobooth Photo Share Page

Minimal Flask app hosted on Render (free tier). Serves a public share page for
each photo with Open Graph meta tags, a download button, and social share links.

## Tech Stack

| Layer      | Library          |
|------------|------------------|
| Web        | Flask 3          |
| WSGI       | Gunicorn         |
| Config     | python-dotenv    |
| Packaging  | uv               |

## Routes

| Method | Path                  | Description                                            |
|--------|-----------------------|--------------------------------------------------------|
| GET    | `/photo/<filename>`   | Share page with OG tags + download + social buttons    |
| GET    | `/healthz`            | Health check (used by Render to verify the service)    |

Any other path returns the custom 404 page.

## Environment Variables (copy `.env.example` → `.env`)

| Variable         | Description                                              |
|------------------|----------------------------------------------------------|
| `R2_PUBLIC_URL`  | Cloudflare R2 public base URL (no trailing slash)        |
| `SITE_URL`       | Public URL of this Render service (no trailing slash)    |

## Installation & Run

### Local development

```bash
cd share_site
uv sync
cp .env.example .env   # fill in real values
uv run flask --app app:create_app run --port 8080
```

### Deploy to Render (one-click)

The included `render.yaml` enables Blueprint deployment:

1. Push the repo to GitHub.
2. In the Render dashboard → **New → Blueprint** → select the repo.
3. Set `R2_PUBLIC_URL` and `SITE_URL` in the Render environment variables.
4. Deploy.

The start command used by Render:

```
uv run gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 30
```

## How It Works

1. `/photo/<filename>` builds the R2 URL: `R2_PUBLIC_URL/filename`.
2. It sends a HEAD request to R2 to confirm the photo exists (returns 404 if not).
3. Renders `photo.html` with:
   - Open Graph + Twitter Card meta tags pointing at the R2 image URL.
   - A download link directly to R2 (no egress cost).
   - Pre-built social share URLs for X (Twitter), Facebook, and WhatsApp.

## File Layout

```
share_site/
├── app.py              Flask app factory + routes
├── templates/
│   ├── photo.html      Share page (OG tags, Bootstrap 5)
│   └── 404.html        Friendly 404 page
├── .env.example
├── render.yaml         Render Blueprint config
└── pyproject.toml
```
