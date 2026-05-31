import datetime
import json
import logging
import os
import re
import threading
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image as PILImage
from flask import Flask, Response, jsonify, redirect, render_template, request
from werkzeug.utils import secure_filename

from camera import Camera, mjpeg_generator
from models import Photo, init_db
from qr_generator import generate_qr
from backgrounds import (
    apply_background, apply_background_ai, background_list,
    delete_background, get_dominant_color, rembg_available, save_background,
)
from themes import apply_theme, theme_list
from uploader import update_photos_json, upload_photo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Module-level singletons — one camera + one DB session factory per process
_camera: Camera | None = None
_Session = None
_last_status: dict = {}
_capture_lock = threading.Lock()


_VALID_EVENTS = {"default", "christmas", "birthday", "graduation", "wedding"}


def _get_event(app: Flask) -> str:
    try:
        data = json.loads((Path(app.root_path) / "event.json").read_text())
        return data.get("event", "default")
    except Exception:
        return "default"


def _set_event(app: Flask, event: str) -> None:
    (Path(app.root_path) / "event.json").write_text(json.dumps({"event": event}))


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)

    # Ensure runtime directories exist
    photos_dir = Path(app.root_path) / "photos"
    qr_dir = Path(app.root_path) / "static" / "qr_codes"
    photos_dir.mkdir(exist_ok=True)
    qr_dir.mkdir(parents=True, exist_ok=True)

    # SQLite via plain SQLAlchemy (works inside and outside request context)
    global _Session
    _Session = init_db(Path(app.root_path) / "photobooth.db")

    # Start camera background thread
    global _camera
    _camera = Camera()
    _camera.start()

    # Optional GPIO button on pin 17 (Pi only)
    _start_gpio(app)

    # ------------------------------------------------------------------ #
    # Routes
    # ------------------------------------------------------------------ #

    @app.route("/")
    def index():
        gallery_url = os.environ.get("PHOTOSLIDE_URL", "")
        return render_template("index.html", gallery_url=gallery_url)

    @app.route("/admin")
    def admin():
        gallery_url = os.environ.get("PHOTOSLIDE_URL", "")
        return render_template("admin.html", gallery_url=gallery_url)

    @app.route("/gallery")
    def gallery():
        gallery_url = os.environ.get("PHOTOSLIDE_URL", "")
        share_site_url = os.environ.get("SHARE_SITE_URL", "").rstrip("/")
        event = _get_event(app)
        with _Session() as session:
            rows = session.query(Photo).order_by(Photo.timestamp.desc()).limit(200).all()
            photos_data = [p.to_dict() for p in rows]
        return render_template("gallery.html",
                               photos=photos_data,
                               gallery_url=gallery_url,
                               share_site_url=share_site_url,
                               event=event)

    @app.route("/photos")
    def photos_redirect():
        return redirect("/gallery", 301)

    @app.route("/api/event", methods=["GET"])
    def get_event_route():
        return jsonify({"event": _get_event(app)})

    @app.route("/api/event", methods=["POST"])
    def set_event_route():
        data = request.get_json(silent=True) or {}
        event = data.get("event", "default")
        if event not in _VALID_EVENTS:
            return jsonify({"error": "Invalid event type"}), 400
        _set_event(app, event)
        return jsonify({"event": event})

    @app.route("/video_feed")
    def video_feed():
        return Response(
            mjpeg_generator(_camera),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.route("/capture", methods=["POST"])
    def capture():
        data = request.get_json(silent=True) or {}
        theme_id = data.get("theme", "classic")
        background_id = data.get("background", "none")
        removal_mode = data.get("removal", "greenscreen")  # "greenscreen" | "ai"
        if not _capture_lock.acquire(blocking=False):
            return jsonify({"error": "A capture is already in progress"}), 409
        try:
            result = _run_capture(app, theme_id, background_id, removal_mode)
            return jsonify(result)
        except Exception as exc:
            logger.exception("Capture failed")
            return jsonify({"error": str(exc)}), 500
        finally:
            _capture_lock.release()

    @app.route("/themes")
    def themes():
        return jsonify(theme_list())

    @app.route("/backgrounds")
    def backgrounds():
        return jsonify(background_list())

    @app.route("/backgrounds/upload", methods=["POST"])
    def backgrounds_upload():
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        f = request.files["file"]
        if not f.filename:
            return jsonify({"error": "Empty filename"}), 400

        # Derive a safe, lowercase, slug-style name from the original filename
        stem = Path(secure_filename(f.filename)).stem
        slug = re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_") or "background"

        try:
            bg = save_background(f.stream, slug)
            return jsonify(bg), 201
        except Exception as exc:
            logger.exception("Background upload failed")
            return jsonify({"error": str(exc)}), 500

    @app.route("/backgrounds/<bg_id>", methods=["DELETE"])
    def backgrounds_delete(bg_id):
        if not re.match(r"^[a-z0-9_-]+$", bg_id):
            return jsonify({"error": "Invalid background id"}), 400
        if delete_background(bg_id):
            return jsonify({"ok": True})
        return jsonify({"error": "Not found"}), 404

    @app.route("/backgrounds/<bg_id>/color")
    def backgrounds_color(bg_id):
        if not re.match(r"^[a-z0-9_-]+$", bg_id):
            return jsonify({"error": "Invalid id"}), 400
        color = get_dominant_color(bg_id)
        if color is None:
            return jsonify({"color": None})
        r, g, b = color
        return jsonify({"color": f"#{r:02x}{g:02x}{b:02x}", "rgb": [r, g, b]})

    @app.route("/api/label", methods=["GET"])
    def get_label():
        try:
            data = json.loads((Path(app.root_path) / "label.json").read_text())
            return jsonify({"text": data.get("text", "PHOTOBOOTH")})
        except Exception:
            return jsonify({"text": "PHOTOBOOTH"})

    @app.route("/api/label", methods=["POST"])
    def set_label():
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        if not text or len(text) > 80:
            return jsonify({"error": "Label must be 1–80 characters"}), 400
        (Path(app.root_path) / "label.json").write_text(json.dumps({"text": text}))
        return jsonify({"text": text})

    @app.route("/capabilities")
    def capabilities():
        return jsonify({"rembg": rembg_available()})

    @app.route("/status")
    def status():
        return jsonify(_last_status)

    return app


# ------------------------------------------------------------------ #
# Core capture logic — callable from route OR GPIO thread
# ------------------------------------------------------------------ #

def _run_capture(
    app: Flask,
    theme_id: str = "none",
    background_id: str = "none",
    removal_mode: str = "greenscreen",
) -> dict:
    global _last_status

    now = datetime.datetime.utcnow()
    filename = f"photo_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    local_path = Path(app.root_path) / "photos" / filename

    # 1. Capture still image
    _camera.capture_photo(str(local_path))

    # 2. Background replacement (before frame so border sits on top)
    if background_id != "none":
        raw = PILImage.open(str(local_path))
        if removal_mode == "ai":
            composited = apply_background_ai(raw, background_id)
        else:
            composited = apply_background(raw, background_id)
        raw.close()
        composited.save(str(local_path), "JPEG", quality=95)
        logger.info("Applied background '%s' (%s) to %s", background_id, removal_mode, filename)

    # 3. Apply theme frame, matched to the background's dominant colour
    if theme_id != "none":
        frame_color = get_dominant_color(background_id) if background_id != "none" else None
        raw = PILImage.open(str(local_path))
        themed = apply_theme(raw, theme_id, frame_color=frame_color)
        raw.close()
        themed.save(str(local_path), "JPEG", quality=95)
        logger.info("Applied theme '%s' (frame_color=%s) to %s", theme_id, frame_color, filename)

    # 4. Upload to Cloudflare R2
    r2_url = upload_photo(str(local_path), filename)
    update_photos_json(filename)

    # 5. Generate QR code pointing at the share page
    share_site_url = os.environ.get("SHARE_SITE_URL", "").rstrip("/")
    share_url = f"{share_site_url}/?f={filename}"
    qr_filename = f"qr_{filename.replace('.jpg', '.png')}"
    qr_path = Path(app.root_path) / "static" / "qr_codes" / qr_filename
    generate_qr(share_url, str(qr_path))

    # 6. Persist to SQLite
    with _Session() as session:
        session.add(Photo(filename=filename, r2_url=r2_url, timestamp=now))
        session.commit()

    result = {
        "filename": filename,
        "r2_url": r2_url,
        "share_url": share_url,
        "qr_url": f"/static/qr_codes/{qr_filename}",
        "timestamp": now.isoformat() + "Z",
    }
    _last_status = result
    logger.info("Capture complete: %s", filename)
    return result


# ------------------------------------------------------------------ #
# Optional GPIO listener (Pi only)
# ------------------------------------------------------------------ #

def _start_gpio(app: Flask) -> None:
    try:
        from gpiozero import Button  # type: ignore[import]
    except ImportError:
        return

    def _handler() -> None:
        if _capture_lock.acquire(blocking=False):
            try:
                _run_capture(app)
            except Exception:
                logger.exception("GPIO capture failed")
            finally:
                _capture_lock.release()

    try:
        btn = Button(17, bounce_time=0.1)
        # Run handler in a daemon thread so gpiozero's callback returns quickly
        btn.when_pressed = lambda: threading.Thread(
            target=_handler, daemon=True
        ).start()
        logger.info("GPIO button listener active on pin 17")
    except Exception:
        logger.warning("GPIO setup failed — running without physical button")


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, threaded=True)
