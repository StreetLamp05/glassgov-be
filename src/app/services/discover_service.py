from __future__ import annotations
from typing import List, Dict, Optional
from threading import Thread

from sqlalchemy import or_, and_

from .. import db
from ..models.governance import Source, Body, Jurisdiction
from ..models.civic import CitizenPost
from ..models.enums import SourceType, Category
from .ner_service import analyze as ner_analyze

CANDIDATE_LABELS = [
    "food_access","road_safety","crime","housing",
    "zoning","transport","budget","health"
]

# ---------- GEO HELPERS ----------
def _normalize_county(county: Optional[str]) -> Optional[str]:
    if not county: return None
    c = county.strip()
    return c if c.lower().endswith("county") else f"{c} County"

def _geo_source_query(city: Optional[str], county: Optional[str], state_name: Optional[str]):
    """
    Union filter across city / county / state using Jurisdiction.
    Matches by:
      - city:  Jurisdiction.level = 'city'   AND Jurisdiction.name ILIKE %city%
      - county:Jurisdiction.level = 'county' AND Jurisdiction.name ILIKE %county%
      - state: Jurisdiction.level = 'state'  AND Jurisdiction.name ILIKE %state_name%
    """
    county = _normalize_county(county)

    q = db.session.query(Source).join(Body, Body.id == Source.body_id).join(
        Jurisdiction, Jurisdiction.id == Body.jurisdiction_id
    )

    clauses = []
    if city:
        clauses.append(and_(Jurisdiction.level == "city", Jurisdiction.name.ilike(f"%{city}%")))
    if county:
        clauses.append(and_(Jurisdiction.level == "county", Jurisdiction.name.ilike(f"%{county}%")))
    if state_name:
        # match either jurisdiction name or state_name field
        clauses.append(and_(Jurisdiction.level == "state", Jurisdiction.name.ilike(f"%{state_name}%")))
        clauses.append(Jurisdiction.state_name.ilike(f"%{state_name}%"))

    return q.filter(or_(*clauses)) if clauses else q.filter(False)

def _geo_posts_query(city: Optional[str], county: Optional[str], state_name: Optional[str]):
    county = _normalize_county(county)
    clauses = []
    if city: clauses.append(CitizenPost.city.ilike(city))
    if county: clauses.append(CitizenPost.county.ilike(county))
    if state_name: clauses.append(CitizenPost.state_name.ilike(state_name))
    return CitizenPost.query.filter(or_(*clauses)) if clauses else CitizenPost.query.filter(False)

# ---------- TOP CATEGORIES ----------
def _top_categories_for_geo(city: Optional[str], county: Optional[str], state_name: Optional[str], limit: int = 3) -> List[Dict]:
    counts = {c: 0 for c in CANDIDATE_LABELS}

    # Gov: count tags within geo
    for (tags,) in _geo_source_query(city, county, state_name).with_entities(Source.tags).all():
        if not tags: continue
        for c in CANDIDATE_LABELS:
            if c in tags: counts[c] += 1

    # Posts: count primary enum within geo
    for (cat_enum,) in _geo_posts_query(city, county, state_name).with_entities(CitizenPost.category).all():
        c = getattr(cat_enum, "value", str(cat_enum))
        if c in counts: counts[c] += 1

    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    top = [{"label": l, "count": n} for l, n in ranked[:limit] if n > 0]
    if not top:
        top = [{"label":"crime","count":0},{"label":"housing","count":0},{"label":"transport","count":0}]
    return top

# ---------- SECTIONS ----------
def _gov_actions_for(city: Optional[str], county: Optional[str], state_name: Optional[str], category: str, limit: int) -> List[Dict]:
    q = _geo_source_query(city, county, state_name).filter(Source.tags != None)  # noqa: E711
    q = q.filter(Source.tags.any(category))
    items = q.order_by(Source.meeting_datetime.desc().nullslast(), Source.created_at.desc()).limit(limit).all()
    return [{
        "id": str(s.id),
        "title": s.title,
        "summary": s.summary,
        "date": s.meeting_datetime.isoformat() if s.meeting_datetime else None,
        "tags": s.tags or [],
        "url": s.url,
        "source_type": s.source_type.value if s.source_type else None,
    } for s in items]

def _citizen_issues_for(city: Optional[str], county: Optional[str], state_name: Optional[str], category: str, limit: int) -> List[Dict]:
    q = _geo_posts_query(city, county, state_name)
    try:
        cat_enum = Category(category)
        q = q.filter(CitizenPost.category == cat_enum)
    except Exception:
        return []
    posts = q.order_by(CitizenPost.score.desc(), CitizenPost.created_at.desc()).limit(limit).all()
    return [{
        "id": str(p.id),
        "title": p.title,
        "score": p.score,
        "created_at": p.created_at.isoformat(),
        "primary_category": p.category.value if hasattr(p.category,'value') else str(p.category),
    } for p in posts]

def _sections(city: Optional[str], county: Optional[str], state_name: Optional[str], categories: List[str], per_category: int) -> List[Dict]:
    return [{
        "category": cat,
        "government_actions": _gov_actions_for(city, county, state_name, cat, per_category),
        "citizen_issues": _citizen_issues_for(city, county, state_name, cat, per_category),
    } for cat in categories]

# ---------- CLASSIFICATION ----------
def _fast_classify(text: str) -> Dict:
    # Use env flags to force rules-only if desired; or extend analyze(use_zero_shot=...)
    return ner_analyze(text)

def _slow_enrich_async(post_id: Optional[str], text: str):
    def _job():
        _ = ner_analyze(text)  # run with ZERO_SHOT=1 in env if you want real enrichment
        # TODO: persist labels/entities later (JSONB column) if desired
    Thread(target=_job, daemon=True).start()

# ---------- PUBLIC ----------
def discover(
    city: Optional[str],
    county: Optional[str],
    state_name: Optional[str],
    message: Optional[str],
    selected_categories: Optional[List[str]],
    per_category: int = 5,
) -> Dict:
    out: Dict = {"geo": {"city": city, "county": county, "state_name": state_name}}

    # 1) Explicit categories
    if selected_categories:
        cats = [c for c in selected_categories if c in CANDIDATE_LABELS]
        out["sections"] = _sections(city, county, state_name, cats, per_category)
        return out

    # 2) Message -> fast classify -> sections for those labels (geo-filtered)
    if message and message.strip():
        fast = _fast_classify(message)
        labels = [c["label"] for c in fast.get("categories", [])][:3] or ["crime","housing","transport"]
        out["fast_classification"] = fast
        out["sections"] = _sections(city, county, state_name, labels, per_category)
        _slow_enrich_async(None, message)
        return out

    # 3) Geo only -> top categories -> sections
    top = _top_categories_for_geo(city, county, state_name, limit=3)
    out["top_categories"] = top
    out["sections"] = _sections(city, county, state_name, [t["label"] for t in top], per_category)
    return out
