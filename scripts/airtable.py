"""Small helper for talking to the Airtable REST API (standard library only).

The token is read from the AIRTABLE_TOKEN environment variable and the base
from AIRTABLE_BASE_ID. Neither is ever written to a file in this repository:
locally they come from .env, on GitHub from Secrets and Variables.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.airtable.com/v0"
TABLE = "Tickets"

# Field names in Airtable (Hebrew, so the client's staff read them naturally)
F_NAME = "שם לקוח"
F_DATE = "תאריך"
F_TYPE = "סוג פנייה"
F_STATUS = "סטטוס טיפול"

TYPES = ["תמיכה טכנית", "חיוב", "מידע כללי", "תלונה"]
STATUSES = ["פתוחה", "בטיפול", "נסגרה"]


def load_dotenv(path=".env"):
    """Read NAME=value lines from .env into the environment, if the file exists."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def config():
    load_dotenv()
    token = os.environ.get("AIRTABLE_TOKEN")
    base = os.environ.get("AIRTABLE_BASE_ID")
    missing = [n for n, v in (("AIRTABLE_TOKEN", token), ("AIRTABLE_BASE_ID", base)) if not v]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}. Copy .env.example to .env and fill it in.")
    return token, base


def request(method, path, token, body=None, query=None):
    url = f"{API}/{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        hint = {401: "token is wrong or revoked", 403: "token lacks a scope or access to this base",
                404: "base or table not found", 422: "request rejected by Airtable's rules"}.get(e.code, "")
        sys.exit(f"Airtable {method} {path} -> HTTP {e.code} {hint}\n{detail}")
