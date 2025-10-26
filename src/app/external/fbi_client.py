import httpx

BASE="https://api.usa.gov/crime/fbi/sapi/api"

class FBIClient:
    def __init__(self, api_key : str | None):
        self.api_key = api_key
        self.client = httpx.Client(base_url="BASE", timeout=10.0)

    def nibrs_offence_by_city(self, state_abbr: str, ori: str, offense: str, since: int, until: int):
        # need to map LA → correct ORI; for MVP we’ll seed geo_context.
        params = {"api_key": self.api_key}
        path = f"/nibrs/{offense}/offense/reported/agencies/state/{state_abbr}/agency/{ori}/offense/reported/{since}/{until}"
        r = self.client.get(path, params=params)
        r.raise_for_status()
        return r.json()