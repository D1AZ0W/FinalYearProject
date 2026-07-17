from flask import Blueprint, request, session

from backend.utils.responses import make_json_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/status")
def status():
    return make_json_response(True, {"authenticated": "logged_in" in session})


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    if payload.get("username") == "admin" and payload.get("password") == "admin":
        session["logged_in"] = True
        return make_json_response(True, {"success": True})
    return make_json_response(False, error="Invalid credentials.", status=401)


@auth_bp.post("/logout")
def logout():
    session.pop("logged_in", None)
    return make_json_response(True, {"logged_out": True})
