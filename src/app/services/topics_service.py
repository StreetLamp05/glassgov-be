from ..models.governance import Source, Body
from ..models.enums import SourceType
from .. import db

def list_sources_for_city(city: str, limit: int = 10):
    # minimal: join via body/jurisdiction names for MVP
    q = db.session.query(Source).join(Body, Body.id == Source.body_id).filter(Body.name.ilike(f"%{city}%"))
    return q.order_by(Source.meeting_datetime.desc().nullslast(), Source.created_at.desc()).limit(limit).all()
