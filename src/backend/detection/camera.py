"""Camera handling and frame generation for the video stream."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import cv2

from backend.config import (
    CLASS_NAMES,
    NO_HELMET_CONF,
    PLATE_CONF,
    PLATE_SAVE_CONF,
    PLATE_MIN_AREA,
    RIDER_CONF,
)
from backend.services.fine_store import FineCandidate
from backend.services.notifications import notify_new_plate

if TYPE_CHECKING:
    from ultralytics import YOLO
    from backend.services.fine_store import FineCaseStore


def _inside(inner: tuple, outer: tuple, margin: int = 10) -> bool:
    """Return True if *inner* bbox is contained within *outer* bbox."""
    ix1, iy1, ix2, iy2 = inner
    ox1, oy1, ox2, oy2 = outer
    return ix1 + margin >= ox1 and iy1 + margin >= oy1 and ix2 <= ox2 and iy2 <= oy2


class SimpleCamera:
    """Wraps an OpenCV VideoCapture, runs YOLO inference per frame, and saves fine cases."""

    def __init__(self, source: str | int, model: "YOLO", device: str, store: "FineCaseStore") -> None:
        self.source = int(source) if str(source).isdigit() else source
        self.model = model
        self.device = device
        self.store = store

        self.capture = cv2.VideoCapture(self.source)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source}")

        fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.frame_delay = 1.0 / fps if fps > 0 else 1.0 / 30
        self.processed_ids: set = set()
        self.is_video = not isinstance(self.source, int)
        print(f"[SimpleCamera] Opened source: {self.source} | FPS: {fps} | Is video: {self.is_video}")

    def process_frame(self) -> bytes | None:
        """Read one frame, run detection, save violations, return JPEG bytes."""
        try:
            ok, frame = self.capture.read()
            if not ok:
                if self.is_video:
                    print("[SimpleCamera] Video ended, restarting…")
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = self.capture.read()
                    if not ok:
                        return None
                else:
                    return None

            results = self.model.predict(
                source=frame, imgsz=640, conf=0.3, iou=0.5,
                device=self.device, verbose=False,
            )

            riders, no_helmets, plates, display_items = [], [], [], []

            for r in results:
                if not r.boxes:
                    continue
                has_ids = hasattr(r.boxes, "id") and r.boxes.id is not None
                ids = r.boxes.id.int().cpu().tolist() if has_ids else [-1] * len(r.boxes)

                for box, tid in zip(r.boxes, ids):
                    coords = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    label = CLASS_NAMES[int(box.cls[0])]
                    bbox = tuple(map(int, coords))

                    display_items.append({"label": label, "bbox": bbox, "conf": conf, "id": tid if tid != -1 else "?"})

                    if label == "rider" and conf >= RIDER_CONF:
                        riders.append((bbox, conf, tid))
                    elif label == "without helmet" and conf >= NO_HELMET_CONF:
                        no_helmets.append((bbox, conf))
                    elif label == "number plate" and conf >= PLATE_CONF:
                        plates.append((bbox, conf))

            # Save violation cases
            for rider_bbox, _, tid in riders:
                if tid not in self.processed_ids:
                    nh_candidates = [(b, c) for b, c in no_helmets if _inside(b, rider_bbox)]
                    pl_candidates = [(b, c) for b, c in plates if _inside(b, rider_bbox)]

                    if nh_candidates and pl_candidates:
                        nh_bbox, nh_conf = max(nh_candidates, key=lambda x: x[1])
                        pl_bbox, pl_conf = max(pl_candidates, key=lambda x: x[1])

                        plate_area = (pl_bbox[2] - pl_bbox[0]) * (pl_bbox[3] - pl_bbox[1])
                        if pl_conf >= PLATE_SAVE_CONF and plate_area >= PLATE_MIN_AREA:
                            candidate = FineCandidate(
                                frame=frame.copy(),
                                frame_idx=0,
                                rider_bbox=rider_bbox,
                                plate_bbox=pl_bbox,
                                no_helmet_conf=nh_conf,
                                plate_conf=pl_conf,
                                overall_conf=(nh_conf + pl_conf) / 2,
                            )
                            row_id = self.store.save_case(candidate, str(self.source))
                            if row_id is not None:
                                self.processed_ids.add(tid)
                                print(f"--- [RECORD SAVED] ID: {tid} | DB Record: {row_id} | Plate Conf: {pl_conf:.2f} ---")
                                notify_new_plate(row_id)

            # Draw bounding boxes on frame
            for item in display_items:
                label, bbox = item["label"], item["bbox"]
                color = (0, 255, 0)
                if label == "without helmet":
                    color = (0, 0, 255)
                elif label == "number plate":
                    color = (255, 255, 0)
                x1, y1, x2, y2 = bbox
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"ID:{item['id']} {label.upper()}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1,
                )

            ok, jpeg = cv2.imencode(".jpg", frame)
            return jpeg.tobytes() if ok else None

        except Exception as exc:
            import traceback
            print(f"[SimpleCamera] Error processing frame: {exc}")
            traceback.print_exc()
            return None

    def stop(self) -> None:
        if self.capture.isOpened():
            self.capture.release()


def frame_generator(source: str | int, store: "FineCaseStore", model: "YOLO", device: str):
    """Generator that yields MJPEG boundary frames for streaming."""
    camera = SimpleCamera(source, model, device, store)
    try:
        while True:
            frame = camera.process_frame()
            if frame:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(camera.frame_delay)
    except GeneratorExit:
        pass
    except Exception as exc:
        import traceback
        print(f"[frame_generator] Error: {exc}")
        traceback.print_exc()
    finally:
        camera.stop()
