from flask import Blueprint, request
from ..services.discover_service import discover

bp = Blueprint("discover", __name__)

@bp.post("/")
def run_discover():
    data = request.get_json(force=True) or {}
    geo = data.get("geo") or {}
    city = geo.get("city")
    county = geo.get("county")
    state_name = geo.get("state_name")
    message = data.get("message")
    categories = data.get("categories")
    per_category = int((data.get("limits") or {}).get("per_category", 5))

    if not (city or county or state_name):
        return {"error": "geo.city, geo.county, or geo.state_name is required"}, 400

    result = discover(
        city=city, county=county, state_name=state_name,
        message=message, selected_categories=categories,
        per_category=per_category,
    )
    return result
