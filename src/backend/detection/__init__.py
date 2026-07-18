"""Detection package — camera streaming and YOLO model helpers."""
from backend.detection.camera import SimpleCamera, frame_generator
from backend.detection.detector import get_device, load_model

__all__ = ["SimpleCamera", "frame_generator", "get_device", "load_model"]
