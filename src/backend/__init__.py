import os

import torch
from flask import Flask
from ultralytics import YOLO

from backend.config import PROJECT_ROOT, WEIGHTS_PATH
from backend.routes import register_routes
from backend.services.fine_store import FineCaseStore


def create_app() -> Flask:
    """Create the HTTP application and register infrastructure dependencies."""
    torch.backends.mkldnn.enabled = False
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "helm_detect_secret_key")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.backends.cudnn.enabled = False

    app.extensions["fine_store"] = FineCaseStore(PROJECT_ROOT)
    app.extensions["detector_model"] = YOLO(WEIGHTS_PATH)
    app.extensions["detector_device"] = device
    register_routes(app)
    return app
