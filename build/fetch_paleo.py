"""Fetch any missing paleo slices into paleo/. Usage: python3 build/fetch_paleo.py"""
import sys
from pathlib import Path

import requests

from paleo import SLICE_AGES, fetch_all

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    sys.exit(fetch_all(root / "paleo", requests.Session(), SLICE_AGES))
