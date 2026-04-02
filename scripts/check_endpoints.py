"""
Simple endpoint checker for local development.

Usage:
    python scripts/check_endpoints.py

Exits with code 0 on success, 2 on failure.
"""
import sys
import json
from urllib.parse import urljoin

import requests

BASE = "http://127.0.0.1:8000"
ENDPOINTS = ["/health", "/test/ml"]


def pretty_print(obj):
    try:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    except Exception:
        print(str(obj))


def main():
    all_ok = True
    for ep in ENDPOINTS:
        url = urljoin(BASE, ep)
        print(f"GET {url}")
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            try:
                data = r.json()
            except ValueError:
                data = r.text
            pretty_print(data)
        except Exception as exc:
            print(f"ERROR: {exc}")
            all_ok = False

    if not all_ok:
        print("One or more endpoints failed.")
        sys.exit(2)
    print("All endpoints responded successfully.")


if __name__ == "__main__":
    main()
