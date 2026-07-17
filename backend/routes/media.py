from pathlib import Path

from flask import Blueprint, abort, send_from_directory

from backend.config import PREDICTIONS_DIR

media_bp = Blueprint("media", __name__)


@media_bp.route("/media/<path:filename>")
def serve_media(filename):
    full = (PREDICTIONS_DIR / filename).resolve()
    if not str(full).startswith(str(PREDICTIONS_DIR)):
        abort(403)
    if not full.exists():
        abort(404)
    return send_from_directory(str(PREDICTIONS_DIR), filename)
