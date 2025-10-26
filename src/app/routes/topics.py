from flask import Blueprint, request
from ..services.topics_service import list_sources_for_city

bp = Blueprint("topics", __name__)

@bp.get("/")
def index():
    city = request.args.get("city", "Los Angeles")
    items = list_sources_for_city(city, limit=10)
    return [{
        "id": str(s.id),
        "title": s.title,
        "summary": s.summary,
        "date": s.meeting_datetime.isoformat() if s.meeting_datetime else None,
        "tags": s.tags or [],
        "url": s.url,
        "source_type": s.source_type.value,
    } for s in items]
