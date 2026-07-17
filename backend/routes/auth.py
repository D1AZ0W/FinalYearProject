from flask import Blueprint, request, session

from backend.utils.responses import api_login_required, make_json_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/status", methods=["GET"])
def api_auth_status():
    return make_json_response(True, {"authenticated": "logged_in" in session})


@auth_bp.route("/login", methods=["POST"])
def api_auth_login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    password = payload.get("password")

    if username == "admin" and password == "admin":
        session["logged_in"] = True
        return make_json_response(True, {"success": True})

    return make_json_response(False, error="Invalid credentials."), 401


@auth_bp.route("/logout", methods=["POST"])
def api_auth_logout():
    session.pop("logged_in", None)
    return make_json_response(True, {"logged_out": True})
