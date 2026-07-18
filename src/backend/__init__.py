"""Flask application factory."""
from __future__ import annotations

from flask import Flask

from backend.config import FLASK_SECRET_KEY, PROJECT_ROOT
from backend.detection.detector import get_device, load_model
from backend.routes import register_routes
from backend.services.fine_store import FineCaseStore


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    # Initialise shared dependencies and attach them to app.extensions
    # so blueprints can access them via current_app.extensions[...].
    app.extensions["detector_device"] = get_device()

    try:
        app.extensions["detector_model"] = load_model()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load YOLO weights. Check WEIGHTS_PATH in config or env.\n  → {exc}"
        ) from exc

    app.extensions["fine_store"] = FineCaseStore(PROJECT_ROOT)

    register_routes(app)
    return app
