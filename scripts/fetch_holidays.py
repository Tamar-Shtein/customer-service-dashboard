"""Bonus: an external public API - Israeli holidays from Hebcal (hebcal.com).

Free, no token needed. Reads the holidays for the next 90 days (Israel
schedule, Hebrew titles) and writes data/holidays.json for the dashboard.

API docs: https://www.hebcal.com/home/195/jewish-calendar-rest-api
Example request:
  https://www.hebcal.com/hebcal?v=1&cfg=json&i=on&lg=he&maj=on&min=on&mod=on
      &start=2026-11-16&end=2027-02-14

Run:  python scripts/fetch_holidays.py
"""
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

DAYS_AHEAD = 90
API = "https://www.hebcal.com/hebcal"

start = date.today()
end = start + timedelta(days=DAYS_AHEAD)
params = {
    "v": 1, "cfg": "json",
    "i": "on",            # Israel schedule (one day of Yom Tov, not two)
    "lg": "he",           # titles in Hebrew
    "maj": "on",          # major holidays
    "min": "on",          # minor holidays
    "mod": "on",          # modern holidays (Yom HaAtzmaut etc.)
    "start": start.isoformat(),
    "end": end.isoformat(),
}
url = f"{API}?{urllib.parse.urlencode(params)}"

try:
    req = urllib.request.Request(url, headers={"User-Agent": "customer-service-dashboard"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
except (urllib.error.URLError, json.JSONDecodeError) as e:
    sys.exit(f"Hebcal request failed: {e}\n{url}")

# The API answers with JSON: {"items": [{"title", "date", "category", "subcat", "yomtov", ...}]}
items = payload.get("items", [])

events, rejected = [], []
for it in items:
    title = (it.get("title") or "").strip()
    d = (it.get("date") or "")[:10]          # some dates carry a time; keep the day
    if not title or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        rejected.append({"item": it, "reason": "missing title or bad date"})
        continue
    if it.get("category") != "holiday":       # skip Rosh Chodesh, parashot etc.
        continue
    events.append({
        "date": d,
        "title": title,
        "kind": it.get("subcat", ""),          # major / minor / modern / fast
        "day_off": bool(it.get("yomtov")),     # Yom Tov: offices are closed
    })

events.sort(key=lambda e: e["date"])
out = {
    "source": "Hebcal API",
    "url": url,
    "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "range": {"start": start.isoformat(), "end": end.isoformat()},
    "items_received": len(items),
    "holidays": events,
    "rejected": rejected,
}
with open("data/holidays.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"Hebcal items received: {len(items)} | holidays kept: {len(events)} | rejected: {len(rejected)}")
for e in events:
    print(f"  {e['date']}  {e['title']}{'  (day off)' if e['day_off'] else ''}")
