from flask import Blueprint, current_app, request

from backend.utils.media import media_url
from backend.utils.responses import api_login_required, make_json_response

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("")
@api_login_required
def dashboard():
    store = current_app.extensions["fine_store"]
    rows = store.get_pending_cases(limit=500, search_query=request.args.get("search", ""), date_filter=request.args.get("date", ""))
    for row in rows:
        row["plate_image_url"] = media_url(row.get("plate_path", ""))
        row["person_image_url"] = media_url(row.get("person_path", ""))
    return make_json_response(True, {"fines": rows, "summary": {"pending_count": len(rows), "latest_case_id": rows[0]["id"] if rows else None}})


@dashboard_bp.post("/close/<int:case_id>")
@api_login_required
def close_case(case_id):
    if current_app.extensions["fine_store"].close_case(case_id):
        return make_json_response(True, {"closed": True})
    return make_json_response(False, error="Case not found or already closed.", status=404)
