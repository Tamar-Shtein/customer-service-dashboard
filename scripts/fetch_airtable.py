"""Read every ticket from Airtable and write data/tickets.json for the dashboard.

Runs on GitHub Actions on a schedule (see .github/workflows/sync-airtable.yml),
or locally:  python scripts/fetch_airtable.py

Rows are checked on the way in ("clean at the door"): a row with a missing
name, a bad date or an unknown type/status is not shown on the dashboard. It
goes to the "rejected" list with the reason, so a person can fix it in Airtable.
"""
import json
import re
import urllib.parse
from datetime import datetime, timezone

from airtable import (F_DATE, F_NAME, F_STATUS, F_TYPE, STATUSES, TABLE, TYPES,
                      config, request)

token, base = config()

raw, offset = [], None
while True:
    q = {"pageSize": 100, **({"offset": offset} if offset else {})}
    page = request("GET", f"{base}/{urllib.parse.quote(TABLE)}", token, query=q)
    raw.extend(page["records"])
    offset = page.get("offset")
    if not offset:
        break

tickets, rejected = [], []
for r in raw:
    f = r["fields"]
    t = {"id": r["id"],
         "name": (f.get(F_NAME) or "").strip(),
         "date": f.get(F_DATE) or "",
         "type": f.get(F_TYPE) or "",
         "status": f.get(F_STATUS) or ""}
    reason = (not t["name"] and "missing customer name") or \
             (not re.fullmatch(r"\d{4}-\d{2}-\d{2}", t["date"]) and "missing or bad date") or \
             (t["type"] not in TYPES and f"unknown type '{t['type']}'") or \
             (t["status"] not in STATUSES and f"unknown status '{t['status']}'")
    if reason:
        rejected.append({"id": r["id"], "reason": reason})
    else:
        tickets.append(t)

tickets.sort(key=lambda t: t["date"], reverse=True)

out = {
    "source": "Airtable",
    "table": TABLE,
    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "rows_in_airtable": len(raw),
    "rows_shown": len(tickets),
    "rejected": rejected,
    "tickets": tickets,
}
with open("data/tickets.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

# Count in, count out: every row is either shown or rejected
assert len(raw) == len(tickets) + len(rejected)
print(f"Rows in Airtable: {len(raw)} | shown: {len(tickets)} | rejected: {len(rejected)}")
for x in rejected:
    print(f"  rejected {x['id']}: {x['reason']}")
