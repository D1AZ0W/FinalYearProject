import time
import traceback

import cv2

from backend.config import CLASS_NAMES, NO_HELMET_CONF, PLATE_CONF, RIDER_CONF
from backend.detection.inference import get_device, get_model, inside_bbox
from backend.services.fine_store import FineCandidate
from backend.services.notifications import notify_new_plate


class SimpleCamera:
    def __init__(self, source, store):
        self.source = int(source) if str(source).isdigit() else source
        self.store = store
        self.model = get_model()
        self.device = get_device()
        self.capture = cv2.VideoCapture(self.source)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source}")

        self.fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.frame_delay = 1.0 / self.fps if self.fps > 0 else 1.0 / 30
        self.processed_ids = set()
        self.is_video = not isinstance(self.source, int)
        print(f"[SimpleCamera] Opened source: {self.source} | FPS: {self.fps} | Is video: {self.is_video}")

    def process_frame(self):
        try:
            ok, frame = self.capture.read()
            if not ok:
                if self.is_video:
                    print("[SimpleCamera] Video ended, restarting...")
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

            riders = []
            no_helmets = []
            plates = []
            display_items = []

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

                    display_id = tid if tid != -1 else "?"
                    display_items.append({"label": label, "bbox": bbox, "conf": conf, "id": display_id})

                    if label == "rider" and conf >= RIDER_CONF:
                        riders.append((bbox, conf, tid))
                    elif label == "without helmet" and conf >= NO_HELMET_CONF:
                        no_helmets.append((bbox, conf))
                    elif label == "number plate" and conf >= PLATE_CONF:
                        plates.append((bbox, conf))

            for rider_bbox, r_conf, tid in riders:
                if tid not in self.processed_ids:
                    nh_candidates = [(b, c) for b, c in no_helmets if inside_bbox(b, rider_bbox)]
                    pl_candidates = [(b, c) for b, c in plates if inside_bbox(b, rider_bbox)]

                    if nh_candidates and pl_candidates:
                        nh_bbox, nh_conf = max(nh_candidates, key=lambda x: x[1])
                        pl_bbox, pl_conf = max(pl_candidates, key=lambda x: x[1])

                        plate_area = (pl_bbox[2] - pl_bbox[0]) * (pl_bbox[3] - pl_bbox[1])
                        if pl_conf > 0.85 and plate_area > 2000:
                            cand = FineCandidate(
                                frame=frame.copy(), frame_idx=0,
                                rider_bbox=rider_bbox, plate_bbox=pl_bbox,
                                no_helmet_conf=nh_conf, plate_conf=pl_conf,
                                overall_conf=(nh_conf + pl_conf) / 2,
                            )
                            row_id = self.store.save_case(cand, str(self.source))
                            self.processed_ids.add(tid)
                            print(f"--- [RECORD SAVED] ID: {tid} | DB Record: {row_id} | Plate Conf: {pl_conf:.2f} ---")
                            if row_id is not None:
                                notify_new_plate(row_id)

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
                    frame, f"ID:{item['id']} {label.upper()}",
                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1,
                )

            ok, jpeg = cv2.imencode(".jpg", frame)
            return jpeg.tobytes() if ok else None
        except Exception as e:
            print(f"[SimpleCamera] Error processing frame: {e}")
            traceback.print_exc()
            return None

    def stop(self):
        if self.capture.isOpened():
            self.capture.release()


def frame_generator(source, store):
    camera = SimpleCamera(source, store)
    try:
        frame_count = 0
        while True:
            frame = camera.process_frame()
            if frame:
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"[frame_generator] Processed {frame_count} frames")
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(camera.frame_delay)
    except GeneratorExit:
        pass
    except Exception as e:
        print(f"[frame_generator] Error: {e}")
        traceback.print_exc()
    finally:
        camera.stop()
