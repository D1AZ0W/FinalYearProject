import os
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent
PREDICTIONS_DIR = (PROJECT_ROOT / "outputs" / "predictions").resolve()


def resolve_project_path(path_value: str) -> str:
    if path_value.isdigit():
        return path_value
    path = Path(path_value)
    return str(path if path.is_absolute() else (PROJECT_ROOT / path).resolve())


VIDEO_SOURCE = resolve_project_path(os.environ.get("VIDEO_SOURCE", "0"))
WEIGHTS_PATH = resolve_project_path(os.environ.get("WEIGHTS_PATH", "outputs/runs/helmet_train/phase1_lr0.00104/weights/best.pt"))
RIDER_CONF = float(os.environ.get("RIDER_CONF", "0.6"))
NO_HELMET_CONF = float(os.environ.get("NO_HELMET_CONF", "0.8"))
PLATE_CONF = float(os.environ.get("PLATE_CONF", "0.7"))
CLASS_NAMES = ["with helmet", "without helmet", "rider", "number plate"]
