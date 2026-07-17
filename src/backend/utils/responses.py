from functools import wraps

from flask import jsonify, session


def make_json_response(success: bool, data=None, error: str | None = None, status: int = 200):
    payload = {"success": success}
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = error
    return jsonify(payload), status


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "logged_in" not in session:
            return jsonify(success=False, error="Unauthorized"), 401
        return view(*args, **kwargs)

    return wrapped
