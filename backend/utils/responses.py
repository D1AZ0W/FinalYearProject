from functools import wraps

from flask import jsonify, session


def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return jsonify(success=False, error="Unauthorized"), 401
        return f(*args, **kwargs)
    return decorated_function


def make_json_response(success: bool, data=None, error=None, status=200):
    payload = {"success": success}
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = error
    return jsonify(payload), status
