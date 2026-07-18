"""Centralised configuration — all paths and tunable constants live here."""
from __future__ import annotations

import os
from pathlib import Path

# --- Paths ---
PACKAGE_DIR: Path = Path(__file__).resolve().parent          # src/backend/
PROJECT_ROOT: Path = PACKAGE_DIR.parent.parent               # project root
PREDICTIONS_DIR: Path = (PROJECT_ROOT / "outputs" / "predictions").resolve()


def _resolve(path_value: str) -> str:
    """Return an absolute path string; pure digits pass through (webcam index)."""
    if path_value.isdigit():
        return path_value
    p = Path(path_value)
    return str(p if p.is_absolute() else (PROJECT_ROOT / p).resolve())


# --- Video / Model ---
VIDEO_SOURCE: str = _resolve(os.environ.get("VIDEO_SOURCE", "0"))
WEIGHTS_PATH: str = _resolve(
    os.environ.get(
        "WEIGHTS_PATH",
        "outputs/runs/helmet_train/phase1_lr0.00104/weights/best.pt",
    )
)

# --- Detection thresholds ---
RIDER_CONF: float = float(os.environ.get("RIDER_CONF", "0.6"))
NO_HELMET_CONF: float = float(os.environ.get("NO_HELMET_CONF", "0.8"))
PLATE_CONF: float = float(os.environ.get("PLATE_CONF", "0.5"))       # min conf to consider a detection a plate
PLATE_SAVE_CONF: float = float(os.environ.get("PLATE_SAVE_CONF", "0.5"))  # min conf to actually save the violation
PLATE_MIN_AREA: int = int(os.environ.get("PLATE_MIN_AREA", "800"))    # min pixel area of plate bbox to save
CLASS_NAMES: list[str] = ["with helmet", "without helmet", "rider", "number plate"]

# --- Database ---
DB_NAME: str = os.environ.get("DB_NAME", "helm_detect")

# --- App ---
FLASK_SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "helm_detect_secret_key")
PORT: int = int(os.environ.get("PORT", "5001"))
