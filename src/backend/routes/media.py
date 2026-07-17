from flask import Blueprint, abort, send_from_directory

from backend.config import PREDICTIONS_DIR

media_bp = Blueprint("media", __name__)


@media_bp.get("/media/<path:filename>")
def media(filename):
    full_path = (PREDICTIONS_DIR / filename).resolve()
    if PREDICTIONS_DIR not in full_path.parents or not full_path.exists():
        abort(404)
    return send_from_directory(PREDICTIONS_DIR, filename)
