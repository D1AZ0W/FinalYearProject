from flask import Blueprint, current_app, request

from backend.utils.responses import api_login_required, make_json_response

records_bp = Blueprint("records", __name__, url_prefix="/api")


@records_bp.route("/records", methods=["GET"])
@api_login_required
def api_records():
    search_query = request.args.get("search", "")
    store = current_app.extensions["fine_store"]
    rows = store.get_all_records(search_query=search_query)
    return make_json_response(True, {"records": rows})


@records_bp.route("/assign_fine/<int:person_id>/<int:case_id>", methods=["POST"])
@api_login_required
def api_assign_fine(person_id: int, case_id: int):
    store = current_app.extensions["fine_store"]
    success = store.assign_fine(person_id, case_id)
    if success:
        return make_json_response(True, {"assigned": True})
    return make_json_response(False, error="Failed to assign fine."), 400
