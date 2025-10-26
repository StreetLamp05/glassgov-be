from flask import Blueprint, request
from ..models.civic import GeoContext

bp = Blueprint("context", __name__)

@bp.get("/")
def ctx():
    city = request.args.get("city")
    state = request.args.get("state_name")
    q = GeoContext.query
    if city: q = q.filter(GeoContext.city.ilike(city))
    if state: q = q.filter(GeoContext.state_name == state)
    g = q.order_by(GeoContext.as_of.desc().nullslast()).first()
    if not g:
        return {"message": "no context"}, 404
    return {
        "city": g.city, "state_name": g.state_name, "zipcode": g.zipcode,
        "crime_index_12mo": float(g.crime_index_12mo) if g.crime_index_12mo is not None else None,
        "median_rent_usd": g.median_rent_usd,
        "median_income_usd": g.median_income_usd,
        "population": g.population,
        "percent_poverty": float(g.percent_poverty) if g.percent_poverty is not None else None,
        "as_of": g.as_of.isoformat() if g.as_of else None
    }
