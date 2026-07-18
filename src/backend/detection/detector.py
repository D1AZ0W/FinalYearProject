"""YOLO model and device initialisation helpers."""
from __future__ import annotations

import torch
from ultralytics import YOLO

from backend.config import WEIGHTS_PATH


def load_model() -> YOLO:
    """Load the YOLO model from the configured weights path."""
    return YOLO(WEIGHTS_PATH)


def get_device() -> str:
    """Return 'cuda' or 'cpu' and configure torch accordingly."""
    torch.backends.mkldnn.enabled = False
    if torch.cuda.is_available():
        torch.backends.cudnn.enabled = False
        print("[detector] Using GPU (CUDA)")
        return "cuda"
    print("[detector] Using CPU (no GPU detected)")
    return "cpu"
