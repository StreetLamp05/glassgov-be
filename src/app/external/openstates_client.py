"""OpenStates API client.

This module provides a small, reusable client for calling the OpenStates API.

Configuration:
- Set `OPENSTATES_API_KEY` in the environment to your OpenStates API key.
- Optionally set `OPENSTATES_BASE_URL` to override the API base URL.

Example:
	from app.external.openstates_client import OpenStatesClient

	client = OpenStatesClient()  # reads API key from OPENSTATES_API_KEY
	legislators = client.get_legislators(state="ny")

Notes:
- The client includes retries for transient failures and raises requests.HTTPError
  for non-2xx responses. It attaches the API key both as a query parameter (apikey)
  and as an X-API-Key header to be compatible with common OpenStates usage patterns.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

DEFAULT_BASE_URL = os.getenv("OPENSTATES_BASE_URL", "https://openstates.org/api/v1/")
DEFAULT_API_KEY = os.getenv("OPENSTATES_API_KEY")


class OpenStatesClient:
	"""Small OpenStates API client.

	Args:
		api_key: API key string. If not provided, the client will look for
			the `OPENSTATES_API_KEY` environment variable.
		base_url: Base URL for the OpenStates API. Defaults to
			the `OPENSTATES_BASE_URL` env var or the public v1 endpoint.
		timeout: Default request timeout in seconds.
	"""

	def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: int = 10):
		self.api_key = api_key or DEFAULT_API_KEY
		self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/") + "/"
		self.timeout = timeout

		self.session = requests.Session()
		retries = Retry(
			total=3,
			backoff_factor=0.3,
			status_forcelist=(429, 500, 502, 503, 504),
			allowed_methods=("GET", "POST"),
		)
		adapter = HTTPAdapter(max_retries=retries)
		self.session.mount("https://", adapter)
		self.session.mount("http://", adapter)

	def _request(self, path: str, params: Optional[Dict[str, Any]] = None, method: str = "GET") -> Any:
		url = urllib.parse.urljoin(self.base_url, path)
		params = dict(params or {})

		headers: Dict[str, str] = {}
		if self.api_key:
			# Add both header and query param for compatibility with different
			# OpenStates deployments / versions.
			headers["X-API-Key"] = self.api_key
			params.setdefault("apikey", self.api_key)

		resp = self.session.request(method, url, params=params, headers=headers, timeout=self.timeout)
		resp.raise_for_status()
		# Most OpenStates endpoints return JSON
		return resp.json()

	# --- Convenience methods ---
	def get_legislators(self, *, state: str, **kwargs) -> Any:
		"""Return legislators in a state.

		Example: client.get_legislators(state='ny')
		"""
		params = {"state": state}
		params.update(kwargs)
		return self._request("legislators/", params=params)

	def get_legislator(self, legislator_id: str) -> Any:
		"""Get a single legislator by OpenStates id.

		Example: client.get_legislator('ocd-person/123...')
		"""
		return self._request(f"legislators/{urllib.parse.quote(legislator_id)}/")

	def search_bills(self, *, state: Optional[str] = None, query: Optional[str] = None, **kwargs) -> Any:
		"""Search bills. Use `state` and/or `query`.

		Example: client.search_bills(state='ny', query='education')
		"""
		params: Dict[str, Any] = {}
		if state:
			params["state"] = state
		if query:
			params["q"] = query
		params.update(kwargs)
		return self._request("bills/", params=params)

	def get_bill(self, bill_id: str) -> Any:
		"""Get a specific bill by id.

		Note: bill_id format depends on OpenStates version; pass the id exactly as
		returned by search endpoints.
		"""
		return self._request(f"bills/{urllib.parse.quote(bill_id)}/")


__all__ = ["OpenStatesClient", "DEFAULT_API_KEY", "DEFAULT_BASE_URL"]

# TODO: TEST