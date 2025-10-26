import httpx

class CensusClient:
    def __init__(self, api_key: str | None):
        self.api_key = api_key
        self.client = httpx.Client(timeout=10.0)

    def acs5_city(self, table_vars: list[str], state_fips: str, place_code: str, year: int = 2022):
        # Example: https://api.census.gov/data/2022/acs/acs5?get=NAME,B19013_001E&for=place:44000&in=state:06
        params = {
            "get": ",".join(table_vars),
            "for": f"place:{place_code}",
            "in": f"state:{state_fips}",
            "key": self.api_key or "",
        }
        url = f"https://api.census.gov/data/{year}/acs/acs5"
        r = self.client.get(url, params=params)
        r.raise_for_status()
        return r.json()
