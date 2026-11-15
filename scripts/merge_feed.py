#!/usr/bin/env python3
"""Merge this run's leads into the published feed.

The bot's own leads.json only holds the finds of one run, so a quiet morning
would replace a good list with a short one. This keeps a rolling window of the
last two weeks instead, so the page always shows the recent leads that are
still open.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KEEP_DAYS = 14
MAX_LEADS = 40


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def posted_within(lead: dict, cutoff: date) -> bool:
    raw = (lead.get("posted") or "")[:10]
    try:
        return date.fromisoformat(raw) >= cutoff
    except ValueError:
        return True


def main(new_path: Path, feed_path: Path) -> int:
    if not new_path.exists():
        print(f"missing this run's leads: {new_path}", file=sys.stderr)
        return 1

    new = load(new_path)
    old = load(feed_path)
    feed_exists = feed_path.exists()

    incoming = [lead for lead in (new.get("leads") or []) if lead.get("url")]
    if feed_exists and not incoming:
        print("no new leads this run - keeping the published list")
        return 0

    rows: dict[str, dict] = {}
    for lead in old.get("leads") or []:
        if lead.get("url"):
            rows[lead["url"]] = dict(lead)

    added = 0
    for lead in incoming:
        previous = rows.get(lead["url"])
        if previous is None:
            added += 1
            rows[lead["url"]] = dict(lead)
        elif (lead.get("score") or 0) >= (previous.get("score") or 0):
            rows[lead["url"]] = dict(lead)

    if feed_exists and added == 0:
        print("nothing new to add - keeping the published list as it is")
        return 0

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=KEEP_DAYS)
    kept = [lead for lead in rows.values() if posted_within(lead, cutoff)]
    kept.sort(key=lambda l: ((l.get("score") or 0), l.get("posted") or ""), reverse=True)
    kept = kept[:MAX_LEADS]

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(kept),
        "leads": kept,
    }
    feed_path.parent.mkdir(parents=True, exist_ok=True)
    feed_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"feed: {len(kept)} lead(s), {added} new this run")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: merge_feed.py <this-run-leads.json> <published-leads.json>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
