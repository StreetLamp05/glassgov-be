import requests
from typing import Dict, List, Any
import os
BASE_URL = "https://v3.openstates.org"
API_KEY = os.getenv("OPENSTATES_API_KEY")
# TODO: FIX API KEY FETCHING, ALSO REQ NEW API KEY
class OpenStatesError(Exception):
    pass

class InvalidAPIKeyError(OpenStatesError):
    pass

JURISDICTION_MAP = {
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
    "district of columbia": "ocd-jurisdiction/country:us/district:dc/government"
}
LATEST_SESSIONS: Dict[str, str] = {}


def get_latest_session(jurisdiction_id: str) -> str:
    """Fetch latest session using updated_desc sort (since session_desc is unsupported)."""
    if jurisdiction_id in LATEST_SESSIONS:
        return LATEST_SESSIONS[jurisdiction_id]

    params = {
        "apikey": API_KEY,
        "jurisdiction": jurisdiction_id,
        "sort": "updated_desc",
        "per_page": 1
    }
    try:
        response = requests.get(f"{BASE_URL}/bills", params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            raise OpenStatesError("No bills found for jurisdiction.")
        latest_session = results[0].get("session")
        if not latest_session:
            raise OpenStatesError("No session field found in result.")
        LATEST_SESSIONS[jurisdiction_id] = latest_session
        return latest_session
    except requests.RequestException as e:
        raise OpenStatesError(f"Failed to fetch latest session: {str(e)}")


def get_bills(jurisdiction: str, q: str = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch recent bills for a jurisdiction and optional keyword."""
    if not API_KEY:
        raise InvalidAPIKeyError("API key required")

    ocd_id = JURISDICTION_MAP.get(jurisdiction.lower())
    if not ocd_id:
        raise ValueError(f"Unknown jurisdiction: {jurisdiction}")

    # Auto-detect session
    session = get_latest_session(ocd_id)

    params = {
        "apikey": API_KEY,
        "jurisdiction": ocd_id,
        "session": session,
        "sort": "updated_desc",
        "per_page": limit
    }
    if q:
        params["q"] = q

    try:
        response = requests.get(f"{BASE_URL}/bills", params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
    except requests.RequestException as e:
        raise OpenStatesError(f"API request failed: {str(e)}")

    bills = []
    for bill in results:
        bills.append({
            "id": bill.get("identifier"),
            "title": bill.get("title"),
            "jurisdiction": bill.get("jurisdiction", {}).get("name", jurisdiction),
            "session": bill.get("session"),
            "latest_action": bill.get("latest_action_date"),
            "subjects": bill.get("subject"),
            "link": bill.get("openstates_url")
        })
    return bills


if __name__ == "__main__":
    try:
        print("=== North Carolina (auto session): Scorpion-related bills ===")
        nc_bills = get_bills("North Carolina", q="scorpion")
        for b in nc_bills:
            print(f"{b['id']}: {b['title']} ({b['latest_action']})")

        print("\n=== California (auto session): Food access bills ===")
        ca_bills = get_bills("California", q="food access")
        for b in ca_bills:
            print(f"{b['id']}: {b['title']} ({b['latest_action']})")
        
        print("\n=== Texas: housing bills ===")
        tx_housing = get_bills("Texas", "housing")
        for b in tx_housing:
            print(f"{b['id']}: {b['title']} ({b['latest_action']})")

    except Exception as e:
        print(f"Error: {e}")