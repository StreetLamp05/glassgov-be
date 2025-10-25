"""Simple test runner for the OpenStates client.

This file is intentionally runnable as a script (python -m or python tests/__init__.py).
It adds the repository `src/` directory to sys.path so `import app...` works from
the project root. The API call is wrapped in a try/except so missing deps or
network issues don't crash the script.
"""

import sys
from pathlib import Path

# Ensure project/src is on sys.path so `import app...` works when running this
# file directly from the repository root.
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Before importing the OpenStates client module file, ensure a minimal `dotenv`
# shim exists if python-dotenv isn't installed. `openstates_client.py` does a
# `from dotenv import load_dotenv` at import time; if the package is missing the
# import will raise. Creating a small module in sys.modules keeps the test
# script runnable without installing extra deps.
import importlib.util
import types

# provide a no-op dotenv.load_dotenv if python-dotenv is not installed
try:
	import dotenv  # type: ignore
except Exception:
	mod = types.ModuleType("dotenv")
	def load_dotenv(path=None):
		return False
	mod.load_dotenv = load_dotenv
	sys.modules["dotenv"] = mod

# Import the OpenStates client module directly from its file so we don't import
# the package `app` (which pulls in Flask and other application dependencies
# not required for this simple test runner).
client_path = src_path / "app" / "external" / "openstates_client.py"
spec = importlib.util.spec_from_file_location("openstates_client", str(client_path))
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

OpenStatesClient = getattr(module, "OpenStatesClient")

client = OpenStatesClient()  # will read OPENSTATES_API_KEY from environment or .env
print("using api_key:", client.api_key)

try:
	data = client.get_legislators(state="ny")
	print(data)
except Exception as exc:
	# Friendly output instead of letting the script raise an uncaught exception.
	print("API call failed (this may be due to missing OPENSTATES_API_KEY, network, or missing deps):")
	print(repr(exc))