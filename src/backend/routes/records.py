from flask import Blueprint, current_app, request

from backend.utils.responses import api_login_required, make_json_response

records_bp = Blueprint("records", __name__, url_prefix="/api")


@records_bp.get("/records")
@api_login_required
def records():
    rows = current_app.extensions["fine_store"].get_all_records(search_query=request.args.get("search", ""))
    return make_json_response(True, {"records": rows})


@records_bp.post("/assign_fine/<int:person_id>/<int:case_id>")
@api_login_required
def assign_fine(person_id, case_id):
    if current_app.extensions["fine_store"].assign_fine(person_id, case_id):
        return make_json_response(True, {"assigned": True})
    return make_json_response(False, error="Failed to assign fine.", status=400)
