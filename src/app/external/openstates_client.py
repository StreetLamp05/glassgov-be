import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from flask import current_app

BASE_URL = "https://v3.openstates.org"

class OpenStatesError(Exception):
    pass

class InvalidAPIKeyError(OpenStatesError):
    pass

class RateLimitError(OpenStatesError):
    pass

# Map “human” jurisdiction names to OCD jurisdiction IDs (state-level).
JURISDICTION_MAP: Dict[str, str] = {
    "alabama": "ocd-jurisdiction/country:us/state:al/government",
    "alaska": "ocd-jurisdiction/country:us/state:ak/government",
    "arizona": "ocd-jurisdiction/country:us/state:az/government",
    "arkansas": "ocd-jurisdiction/country:us/state:ar/government",
    "california": "ocd-jurisdiction/country:us/state:ca/government",
    "colorado": "ocd-jurisdiction/country:us/state:co/government",
    "connecticut": "ocd-jurisdiction/country:us/state:ct/government",
    "delaware": "ocd-jurisdiction/country:us/state:de/government",
    "florida": "ocd-jurisdiction/country:us/state:fl/government",
    "georgia": "ocd-jurisdiction/country:us/state:ga/government",
    "hawaii": "ocd-jurisdiction/country:us/state:hi/government",
    "idaho": "ocd-jurisdiction/country:us/state:id/government",
    "illinois": "ocd-jurisdiction/country:us/state:il/government",
    "indiana": "ocd-jurisdiction/country:us/state:in/government",
    "iowa": "ocd-jurisdiction/country:us/state:ia/government",
    "kansas": "ocd-jurisdiction/country:us/state:ks/government",
    "kentucky": "ocd-jurisdiction/country:us/state:ky/government",
    "louisiana": "ocd-jurisdiction/country:us/state:la/government",
    "maine": "ocd-jurisdiction/country:us/state:me/government",
    "maryland": "ocd-jurisdiction/country:us/state:md/government",
    "massachusetts": "ocd-jurisdiction/country:us/state:ma/government",
    "michigan": "ocd-jurisdiction/country:us/state:mi/government",
    "minnesota": "ocd-jurisdiction/country:us/state:mn/government",
    "mississippi": "ocd-jurisdiction/country:us/state:ms/government",
    "missouri": "ocd-jurisdiction/country:us/state:mo/government",
    "montana": "ocd-jurisdiction/country:us/state:mt/government",
    "nebraska": "ocd-jurisdiction/country:us/state:ne/government",
    "nevada": "ocd-jurisdiction/country:us/state:nv/government",
    "new hampshire": "ocd-jurisdiction/country:us/state:nh/government",
    "new jersey": "ocd-jurisdiction/country:us/state:nj/government",
    "new mexico": "ocd-jurisdiction/country:us/state:nm/government",
    "new york": "ocd-jurisdiction/country:us/state:ny/government",
    "north carolina": "ocd-jurisdiction/country:us/state:nc/government",
    "north dakota": "ocd-jurisdiction/country:us/state:nd/government",
    "ohio": "ocd-jurisdiction/country:us/state:oh/government",
    "oklahoma": "ocd-jurisdiction/country:us/state:ok/government",
    "oregon": "ocd-jurisdiction/country:us/state:or/government",
    "pennsylvania": "ocd-jurisdiction/country:us/state:pa/government",
    "rhode island": "ocd-jurisdiction/country:us/state:ri/government",
    "south carolina": "ocd-jurisdiction/country:us/state:sc/government",
    "south dakota": "ocd-jurisdiction/country:us/state:sd/government",
    "tennessee": "ocd-jurisdiction/country:us/state:tn/government",
    "texas": "ocd-jurisdiction/country:us/state:tx/government",
    "utah": "ocd-jurisdiction/country:us/state:ut/government",
    "vermont": "ocd-jurisdiction/country:us/state:vt/government",
    "virginia": "ocd-jurisdiction/country:us/state:va/government",
    "washington": "ocd-jurisdiction/country:us/state:wa/government",
    "west virginia": "ocd-jurisdiction/country:us/state:wv/government",
    "wisconsin": "ocd-jurisdiction/country:us/state:wi/government",
    "wyoming": "ocd-jurisdiction/country:us/state:wy/government",
    "district of columbia": "ocd-jurisdiction/country:us/district:dc/government",
}

# simple in-proc cache for the latest session per jurisdiction_id
_LATEST_SESSIONS: Dict[str, str] = {}

DEFAULT_TIMEOUT = 10.0

def _headers() -> Dict[str, str]:
    # Prefer Flask config, fallback to env var
    api_key = current_app.config.get("OPENSTATES_API_KEY") if current_app else os.getenv("OPENSTATES_API_KEY")
    if not api_key:
        raise InvalidAPIKeyError("OPENSTATES_API_KEY not configured")
    return {"X-API-KEY": api_key}

def _request(method: str, path: str, *, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    try:
        r = requests.request(method, url, headers=_headers(), params=params, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as e:
        raise OpenStatesError(f"Network error: {e}") from e

    if r.status_code == 401:
        raise InvalidAPIKeyError("OpenStates API key invalid or missing")
    if r.status_code == 429:
        # honor Retry-After if present
        ra = int(r.headers.get("Retry-After", "1"))
        time.sleep(min(ra, 5))
        raise RateLimitError("OpenStates rate limit hit")
    if r.status_code >= 400:
        raise OpenStatesError(f"OpenStates error {r.status_code}: {r.text}")

    return r.json()

def _normalize_bill(b: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize fields we actually use in the app
    return {
        "id": (b.get("identifier") or b.get("id")),
        "title": b.get("title"),
        "jurisdiction": (b.get("jurisdiction") or {}).get("name"),
        "session": b.get("session"),
        "latest_action": b.get("latest_action_date"),
        "subjects": b.get("subject"),
        "url": b.get("openstates_url"),
        "raw": b,  # keep for persistence if you want
    }

def get_latest_session(jurisdiction_id: str) -> str:
    """Get the latest session string for a jurisdiction_id (OCD)."""
    if jurisdiction_id in _LATEST_SESSIONS:
        return _LATEST_SESSIONS[jurisdiction_id]

    params = {
        "jurisdiction_id": jurisdiction_id,  # <-- correct param for OCD
        "sort": "updated_desc",
        "per_page": 1,
    }
    data = _request("GET", "/bills", params=params)
    results = data.get("results") or []
    if not results:
        raise OpenStatesError("No bills found for jurisdiction to infer session")
    session = results[0].get("session")
    if not session:
        raise OpenStatesError("No session field on latest bill")
    _LATEST_SESSIONS[jurisdiction_id] = session
    return session

def get_bills(jurisdiction: str, q: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch recent bills for a state “jurisdiction” (e.g., 'California').
    Uses OCD jurisdiction_id under the hood and auto-detects current session.
    """
    ocd_id = JURISDICTION_MAP.get(jurisdiction.lower())
    if not ocd_id:
        raise ValueError(f"Unknown jurisdiction: {jurisdiction}")

    session = get_latest_session(ocd_id)
    params: Dict[str, Any] = {
        "jurisdiction_id": ocd_id,
        "session": session,
        "sort": "updated_desc",
        "per_page": limit,
    }
    if q:
        params["q"] = q

    data = _request("GET", "/bills", params=params)
    results = data.get("results") or []
    return [_normalize_bill(b) for b in results]

def search_bills_raw(**params) -> Dict[str, Any]:
    """
    Escape hatch if you want to pass-through query params directly.
    You still get headers + error handling.
    """
    return _request("GET", "/bills", params=params)
