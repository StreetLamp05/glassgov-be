from flask import Blueprint, request
from ..external.openstates_client import get_bills, OpenStatesError

bp = Blueprint("openstates_demo", __name__)

@bp.get("/bills")
def bills():
    j = request.args.get("jurisdiction", "California")
    q = request.args.get("q")
    n = int(request.args.get("limit", "5"))
    try:
        items = get_bills(j, q, n)
        return {"results": items}
    except OpenStatesError as e:
        return {"error": str(e)}, 502
