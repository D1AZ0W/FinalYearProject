import torch
from ultralytics import YOLO

from backend.config import WEIGHTS_PATH

_device: str | None = None
_model: YOLO | None = None


def get_device() -> str:
    global _device
    if _device is None:
        torch.backends.mkldnn.enabled = False
        if torch.cuda.is_available():
            _device = "cuda"
            torch.backends.cudnn.enabled = False
            print(" Using GPU (CUDA)")
        else:
            _device = "cpu"
            print(" Using CPU (No GPU detected)")
    return _device


def get_model() -> YOLO:
    global _model
    if _model is None:
        get_device()
        _model = YOLO(WEIGHTS_PATH)
    return _model


def inside_bbox(inner, outer, margin: int = 10) -> bool:
    ix1, iy1, ix2, iy2 = inner
    ox1, oy1, ox2, oy2 = outer
    return ix1 + margin >= ox1 and iy1 + margin >= oy1 and ix2 <= ox2 and iy2 <= oy2
