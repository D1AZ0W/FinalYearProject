import queue

from flask import Blueprint, Response, current_app, request

from backend.config import VIDEO_SOURCE
from backend.detection.camera import frame_generator
from backend.services.notifications import event_queues
from backend.utils.responses import api_login_required

stream_bp = Blueprint("stream", __name__)


@stream_bp.get("/video_feed")
@api_login_required
def video_feed():
    source = request.args.get("source", VIDEO_SOURCE)
    return Response(frame_generator(source, current_app.extensions["fine_store"], current_app.extensions["detector_model"], current_app.extensions["detector_device"]), mimetype="multipart/x-mixed-replace; boundary=frame")


@stream_bp.get("/stream_notifications")
@api_login_required
def stream_notifications():
    def stream():
        event_queue = queue.Queue(maxsize=20)
        event_queues.append(event_queue)
        try:
            while True:
                yield event_queue.get()
        except GeneratorExit:
            pass
        finally:
            if event_queue in event_queues:
                event_queues.remove(event_queue)

    return Response(stream(), mimetype="text/event-stream")
