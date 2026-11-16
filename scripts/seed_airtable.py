"""One-time setup: create the Tickets table in Airtable and load the 30 tickets.

Run once:  python scripts/seed_airtable.py
Safe to run twice (idempotent): it skips creating the table if it exists, and
skips tickets that are already there (matched on name + date + type).
"""
import json
import urllib.parse

from airtable import (F_DATE, F_NAME, F_STATUS, F_TYPE, STATUSES, TABLE, TYPES,
                      config, request)

token, base = config()

# 1. Create the table if it does not exist yet
schema = request("GET", f"meta/bases/{base}/tables", token)
names = [t["name"] for t in schema["tables"]]
if TABLE in names:
    print(f"Table '{TABLE}' already exists - not creating it again.")
else:
    request("POST", f"meta/bases/{base}/tables", token, {
        "name": TABLE,
        "description": "פניות שירות לקוחות - המקור של הדאשבורד",
        "fields": [
            {"name": F_NAME, "type": "singleLineText"},
            {"name": F_DATE, "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": F_TYPE, "type": "singleSelect",
             "options": {"choices": [{"name": t} for t in TYPES]}},
            {"name": F_STATUS, "type": "singleSelect",
             "options": {"choices": [{"name": s} for s in STATUSES]}},
        ],
    })
    print(f"Created table '{TABLE}'.")

# 2. Read what is already there, so a second run does not double anything
existing, offset = set(), None
while True:
    q = {"pageSize": 100, **({"offset": offset} if offset else {})}
    page = request("GET", f"{base}/{urllib.parse.quote(TABLE)}", token, query=q)
    for r in page["records"]:
        f = r["fields"]
        existing.add((f.get(F_NAME), f.get(F_DATE), f.get(F_TYPE)))
    offset = page.get("offset")
    if not offset:
        break

# 3. Add the tickets that are missing, 10 at a time (Airtable's limit per request)
with open("data/seed_tickets.json", encoding="utf-8") as f:
    seed = json.load(f)
todo = [t for t in seed if (t["name"], t["date"], t["type"]) not in existing]
for i in range(0, len(todo), 10):
    batch = [{"fields": {F_NAME: t["name"], F_DATE: t["date"],
                         F_TYPE: t["type"], F_STATUS: t["status"]}} for t in todo[i:i + 10]]
    request("POST", f"{base}/{urllib.parse.quote(TABLE)}", token, {"records": batch, "typecast": False})

print(f"In seed file: {len(seed)} | already in Airtable: {len(seed) - len(todo)} | added now: {len(todo)}")
