import queue

from flask import Blueprint, Response, current_app, request

from backend.config import VIDEO_SOURCE
from backend.detection.camera import frame_generator
from backend.services.notifications import event_queues
from backend.utils.responses import api_login_required

stream_bp = Blueprint("stream", __name__)


@stream_bp.route("/video_feed")
def video_feed():
    src = request.args.get("source", VIDEO_SOURCE)
    store = current_app.extensions["fine_store"]
    return Response(
        frame_generator(src, store),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@stream_bp.route("/stream_notifications")
@api_login_required
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

    return Response(stream(), mimetype="text/event-stream")
