import logging
import os
import urllib.error
import urllib.request
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask, abort, render_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config.update(
        R2_PUBLIC_URL=os.environ.get("R2_PUBLIC_URL", "").rstrip("/"),
        SITE_URL=os.environ.get("SITE_URL", "").rstrip("/"),
    )

    # ------------------------------------------------------------------ #
    # Routes
    # ------------------------------------------------------------------ #

    @app.route("/photo/<path:filename>")
    def photo(filename: str):
        r2_base = app.config["R2_PUBLIC_URL"]
        site_url = app.config["SITE_URL"]

        r2_url = f"{r2_base}/{filename}"
        share_url = f"{site_url}/photo/{filename}"

        # Verify the photo actually exists in R2 before rendering the page
        if not _r2_photo_exists(r2_url):
            abort(404)

        # Pre-build social share URLs (percent-encoded)
        tweet_url = (
            "https://twitter.com/intent/tweet"
            f"?url={quote(share_url, safe='')}"
            f"&text={quote('Check out my photobooth photo!', safe='')}"
        )
        fb_url = (
            f"https://www.facebook.com/sharer/sharer.php"
            f"?u={quote(share_url, safe='')}"
        )
        wa_url = (
            f"https://wa.me/"
            f"?text={quote('Check out my photobooth photo! ' + share_url, safe='')}"
        )

        return render_template(
            "photo.html",
            r2_url=r2_url,
            share_url=share_url,
            filename=filename,
            tweet_url=tweet_url,
            fb_url=fb_url,
            wa_url=wa_url,
        )

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.errorhandler(404)
    def not_found(exc):
        return render_template("404.html"), 404

    return app


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _r2_photo_exists(url: str) -> bool:
    """HEAD-check the R2 URL. Returns False on 404 or network error."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(req, timeout=5)
        return True
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        logger.warning("HEAD %s returned HTTP %s", url, exc.code)
        return False
    except Exception:
        logger.warning("HEAD check failed for %s", url, exc_info=True)
        return False
