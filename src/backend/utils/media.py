from pathlib import Path

from backend.config import PREDICTIONS_DIR


def media_url(absolute_path: str) -> str:
    if not absolute_path:
        return ""
    try:
        relative_path = Path(absolute_path).resolve().relative_to(PREDICTIONS_DIR)
    except ValueError:
        return ""
    return f"/media/{relative_path.as_posix()}"
