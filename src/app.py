import os
from pathlib import Path
from functools import wraps

import cv2
import torch
from flask import Flask, Response, abort, redirect, render_template, request, send_from_directory, url_for, session, flash
from ultralytics import YOLO

from fine_capture import FineCandidate, FineCaseStore


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PREDICTIONS_DIR = (PROJECT_ROOT / "outputs" / "predictions").resolve()


def _resolve_project_path(path_value: str) -> str:
    if path_value.isdigit():
        return path_value
    p = Path(path_value)
    return str(p if p.is_absolute() else (PROJECT_ROOT / p).resolve())


# Default video source to 0 (laptop camera) as requested
VIDEO_SOURCE = _resolve_project_path(os.environ.get("VIDEO_SOURCE", "0"))
WEIGHTS_PATH = _resolve_project_path(
    os.environ.get("WEIGHTS_PATH", "outputs/runs/helmet_train/phase1_lr0.00104/weights/best.pt")
)

RIDER_CONF = float(os.environ.get("RIDER_CONF", "0.6"))
NO_HELMET_CONF = float(os.environ.get("NO_HELMET_CONF", "0.8"))
PLATE_CONF = float(os.environ.get("PLATE_CONF", "0.7"))

if torch.cuda.is_available():
    DEVICE = "cuda"
    print(" Using GPU (CUDA)")
elif torch.backends.mps.is_available():
    DEVICE = "mps"
    print(" Using Apple MPS")
else:
    DEVICE = "cpu"
    print(" Using CPU (No GPU detected)")

CLASS_NAMES = ["with helmet", "without helmet", "rider", "number plate"]

app = Flask(__name__)
app.secret_key = "helm_detect_secret_key"  # For session management

store = FineCaseStore(PROJECT_ROOT)
model = YOLO(WEIGHTS_PATH)


# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def _inside(inner, outer, margin=10):
    ix1, iy1, ix2, iy2 = inner
    ox1, oy1, ox2, oy2 = outer
    return ix1 + margin >= ox1 and iy1 + margin >= oy1 and ix2 <= ox2 and iy2 <= oy2
import threading
import time
import queue

# --- Global Event Queues for SSE Notifications ---
event_queues = []

def notify_new_plate(case_id):
    msg = f"data: {{\"case_id\": {case_id}}}\n\n"
    for q in event_queues:
        try:
            q.put_nowait(msg)
        except queue.Full:
            pass

# --- Threaded Camera Handling ---
class ThreadedCamera:
    def __init__(self, source):
        # Convert digit to int for camera index
        self.source = int(source) if str(source).isdigit() else source
        self.capture = cv2.VideoCapture(self.source)
        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source}")
        
        self.frame = None
        self.raw_frame = None
        self.results = []
        self.active_candidates = {}  # track_id -> FineCandidate
        self.processed_ids = set()    # track_ids already saved to DB
        self.running = True
        self.lock = threading.Lock()
        
        # Start threads
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.inference_thread.start()

    def _capture_loop(self):
        while self.running:
            ok, frame = self.capture.read()
            if ok:
                with self.lock:
                    self.raw_frame = frame.copy()
            else:
                if isinstance(self.source, int):
                    time.sleep(1.0)
                    continue
                else:
                    print(f"Video source {self.source} reached the end. Stopping.")
                    self.running = False
                    break
            time.sleep(0.01)

    def _inference_loop(self):
        global model
        frame_idx = 0
        while self.running:
            local_frame = None
            with self.lock:
                if self.raw_frame is not None:
                    local_frame = self.raw_frame.copy()
            
            if local_frame is not None:
                frame_idx += 1
                res_list = list(model.track(
                    source=local_frame, persist=True, imgsz=640, conf=0.3, iou=0.5, 
                    stream=True, device=DEVICE, tracker="botsort.yaml", verbose=False
                ))
                
                new_display_items = []
                riders = []
                no_helmets = []
                plates = []
                current_frame_ids = set()

                for r in res_list:
                    if not r.boxes or r.boxes.id is None: continue
                    ids = r.boxes.id.int().cpu().tolist()
                    for box, tid in zip(r.boxes, ids):
                        coords = box.xyxy[0].tolist()
                        conf = float(box.conf[0])
                        label = CLASS_NAMES[int(box.cls[0])]
                        bbox = tuple(map(int, coords))
                        current_frame_ids.add(tid)
                        new_display_items.append({"label": label, "bbox": bbox, "conf": conf, "id": tid})

                        if label == "rider" and conf >= RIDER_CONF:
                            riders.append((bbox, conf, tid))
                        elif label == "without helmet" and conf >= NO_HELMET_CONF:
                            no_helmets.append((bbox, conf))
                        elif label == "number plate" and conf >= PLATE_CONF:
                            plates.append((bbox, conf))

                for rider_bbox, r_conf, tid in riders:
                    if tid in self.processed_ids: continue
                    nh_candidates = [(b, c) for b, c in no_helmets if _inside(b, rider_bbox)]
                    pl_candidates = [(b, c) for b, c in plates if _inside(b, rider_bbox)]
                    
                    if nh_candidates and pl_candidates:
                        nh_bbox, nh_conf = max(nh_candidates, key=lambda x: x[1])
                        pl_bbox, pl_conf = max(pl_candidates, key=lambda x: x[1])
                        
                        new_cand = FineCandidate(
                            frame=local_frame.copy(), frame_idx=frame_idx,
                            rider_bbox=rider_bbox, plate_bbox=pl_bbox,
                            no_helmet_conf=nh_conf, plate_conf=pl_conf, overall_conf=(nh_conf + pl_conf) / 2
                        )
                        
                        plate_area = (pl_bbox[2] - pl_bbox[0]) * (pl_bbox[3] - pl_bbox[1])
                        if pl_conf > 0.85 and plate_area > 2000:
                            self._save_candidate(tid, new_cand)
                            if tid in self.active_candidates: del self.active_candidates[tid]
                        else:
                            if tid not in self.active_candidates or pl_conf > self.active_candidates[tid].plate_conf:
                                self.active_candidates[tid] = new_cand

                finished_ids = [tid for tid in self.active_candidates if tid not in current_frame_ids]
                for tid in finished_ids:
                    self._save_candidate(tid, self.active_candidates.pop(tid))

                with self.lock:
                    self.results = new_display_items
            time.sleep(0.001)
        self.flush_active_tracks()

    def _save_candidate(self, tid, cand):
        row_id = store.save_case(cand, str(self.source))
        self.processed_ids.add(tid)
        print(f"--- [RECORD SAVED] ID: {tid} | DB Record: {row_id} | Plate Conf: {cand.plate_conf:.2f} ---")
        notify_new_plate(row_id)

    def flush_active_tracks(self):
        for tid, cand in list(self.active_candidates.items()):
            if tid not in self.processed_ids:
                self._save_candidate(tid, cand)
        self.active_candidates.clear()

    def get_frame(self):
        with self.lock:
            if self.raw_frame is None: return None
            img, current_results = self.raw_frame.copy(), list(self.results)
        
        for item in current_results:
            label, bbox, color = item["label"], item["bbox"], (0, 255, 0)
            if label == "without helmet": color = (0, 0, 255)
            elif label == "number plate": color = (255, 255, 0)
            x1, y1, x2, y2 = bbox
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, f"ID:{item['id']} {label.upper()}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        ok, jpeg = cv2.imencode(".jpg", img)
        return jpeg.tobytes() if ok else None

    def stop(self):
        self.running = False
        self.flush_active_tracks()
        if self.capture.isOpened(): self.capture.release()

# Global camera instance
current_camera = None

def frame_generator(source):
    global current_camera
    
    if current_camera is not None:
        if current_camera.source != source:
            current_camera.stop()
            current_camera = ThreadedCamera(source)
    else:
        current_camera = ThreadedCamera(source)
    
    while True:
        frame = current_camera.get_frame()
        if frame:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        time.sleep(0.03) # ~30 FPS feed


def _media_url(abs_path: str) -> str:
    if not abs_path:
        return ""
    p = Path(abs_path).resolve()
    try:
        # Check relative to PROJECT_ROOT, specifically outputs/predictions
        rel = p.relative_to(PREDICTIONS_DIR)
    except ValueError:
        return ""
    return f"/media/{rel.as_posix()}"


# --- Routes ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Specific values as requested by user
        if username == "admin" and password == "admin":
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials. Personnel only.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    src = request.args.get("source", VIDEO_SOURCE)
    return render_template("index.html", current=src)


@app.route("/dashboard")
@login_required
def dashboard():
    search_query = request.args.get("search", "")
    date_filter = request.args.get("date", "")
    rows = store.get_pending_cases(limit=500, search_query=search_query, date_filter=date_filter)
    for row in rows:
        row["plate_image_url"] = _media_url(row.get("plate_path", ""))
        row["person_image_url"] = _media_url(row.get("person_path", ""))
    return render_template("dashboard.html", rows=rows)


@app.route("/records")
@login_required
def records():
    # Use 'plate' as the general search term. 
    # If it's a generic placeholder, we show all records instead of an empty table.
    search_query = request.args.get("plate", "").strip()
    if search_query.upper() in ["ID REQUIRED", "ID REQ", "PENDING_OCR", "MANUAL ID REQUIRED"]:
        search_query = ""

    plate_img = request.args.get("plate_img", "")
    case_id = request.args.get("case_id", "")
    all_recs = store.get_all_records(search_query=search_query)
    return render_template("records.html", 
                           records=all_recs, 
                           lookup_plate_img=plate_img, 
                           case_id=case_id)


@app.post("/assign_fine/<int:person_id>/<int:case_id>")
@login_required
def assign_fine(person_id: int, case_id: int):
    success = store.assign_fine(person_id, case_id)
    if success:
        flash("Fine assigned and case closed successfully!")
    else:
        flash("Failed to assign fine. Record not found.")
    return redirect(url_for("dashboard"))


@app.post("/dashboard/close/<int:case_id>")
@login_required
def close_case(case_id: int):
    store.close_case(case_id)
    return redirect(url_for("dashboard"))


@app.route("/media/<path:filename>")
def media(filename):
    full = (PREDICTIONS_DIR / filename).resolve()
    if not str(full).startswith(str(PREDICTIONS_DIR)):
        abort(403)
    if not full.exists():
        abort(404)
    return send_from_directory(str(PREDICTIONS_DIR), filename)


@app.route("/video_feed")
def video_feed():
    src = request.args.get("source", VIDEO_SOURCE)
    return Response(frame_generator(src), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/stream_notifications")
@login_required
def stream_notifications():
    def stream():
        q = queue.Queue(maxsize=20)
        event_queues.append(q)
        try:
            while True:
                msg = q.get()
                yield msg
        except GeneratorExit:
            if q in event_queues:
                event_queues.remove(q)
    return Response(stream(), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True, threaded=True)
