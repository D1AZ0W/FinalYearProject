from pathlib import Path

from backend.config import PREDICTIONS_DIR


def media_url(abs_path: str) -> str:
    if not abs_path:
        return ""
    p = Path(abs_path).resolve()
    try:
        rel = p.relative_to(PREDICTIONS_DIR)
    except ValueError:
        return ""
    return f"/media/{rel.as_posix()}"
