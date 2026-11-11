"""Timezone-aware schedules. Background jobs never approve or install."""
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import config as preferences
from .core import ScoutError, digest, identifier, now
from .github import GitHub

DAYS = {n: i for i, n in enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"])}


def make(name, source, at, zone, days):
    identifier(name)
    if source not in {"github", "instagram", "all"}:
        raise ScoutError("Unsupported schedule source")
    try:
        h, m = map(int, at.split(":"))
        if not (0 <= h < 24 and 0 <= m < 60):
            raise ValueError()
        ZoneInfo(zone)
        weekdays = sorted({DAYS[d.strip().lower()] for d in days.split(",")}) if days != "daily" else list(range(7))
    except (ValueError, KeyError, ZoneInfoNotFoundError) as exc:
        raise ScoutError("Use HH:MM, an IANA timezone, and daily or mon,tue,...") from exc
    return {"name": name, "source": source, "at": f"{h:02d}:{m:02d}", "timezone": zone,
            "days": weekdays, "enabled": True}


def slots(job, current, before=1, after=35):
    zone = ZoneInfo(job["timezone"])
    day = current.astimezone(zone).date()
    h, m = map(int, job["at"].split(":"))
    found = []
    for offset in range(-before, after + 1):
        date = day + timedelta(days=offset)
        if date.weekday() not in job["days"]:
            continue
        local = datetime(date.year, date.month, date.day, h, m, tzinfo=zone, fold=0)
        utc = local.astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None) != local.replace(tzinfo=None):
            continue
        found.append(utc)
    return found


def upcoming(job, current=None):
    current = current or datetime.now(timezone.utc)
    return [t.astimezone(ZoneInfo(job["timezone"])).isoformat()
            for t in slots(job, current) if t > current][:5]


def run(store, config, source, client=None, mode="best-match"):
    from .github import discover as github_discover
    from .instagram import discover as instagram_discover
    from .reports import write_report
    results, failures = [], []
    gh = client or GitHub()
    for selected in (["github", "instagram"] if source == "all" else [source]):
        try:
            if selected == "github":
                results.append(github_discover(store, config, config["budgets"]["candidates"], gh, mode))
            else:
                results.append(instagram_discover(store, config))
        except ScoutError as exc:
            failures.append({"source": selected, "error": str(exc)})
    updates = []
    for entry in store.list("installed")[:20]:
        try:
            revision = gh.revision(entry["repository"])
            if revision != entry["revision"]:
                updates.append({"repository": entry["repository"], "installed_revision": entry["revision"],
                                "latest_revision": revision, "status": "new_inspection_required"})
        except ScoutError:
            updates.append({"repository": entry["repository"], "status": "update_check_unavailable"})
    prepared = []
    if config["model"].get("enabled"):
        from .proposals import prepare
        from .reviewer import model_review
        candidates = [r for result in results for r in result.get("candidates", [])]
        # Explicit repository links from creator captions join the same inspection queue.
        linked = [repo for result in results for post in result.get("new_posts", [])
                  for repo in post.get("github_candidates", [])]
        candidates += [{"repository": repo} for repo in dict.fromkeys(linked)]
        candidates = list({r["repository"].lower(): r for r in candidates}.values())
        known = {p["repository"] for p in store.list("proposals")
                 if p.get("status") not in {"rolled_back", "rejected"}}
        for row in [r for r in candidates if r["repository"] not in known][:config["budgets"]["model_calls"]]:
            try:
                p = prepare(store, config, row["repository"])
                if p.get("id"):
                    p = model_review(store, config, p["id"])
                prepared.append({k: p.get(k) for k in ("id", "status", "assessment", "next")})
            except ScoutError as exc:
                prepared.append({"repository": row["repository"], "status": "unverified", "reason": str(exc)})
    result = {"id": "scan-" + digest([now(), source])[:16], "at": now(), "source": source,
              "results": results, "failures": failures, "updates": updates, "prepared_reviews": prepared,
              "status": "completed" if not failures else "partial" if results else "failed",
              "next": "Review against your setup, inspect a pinned package, then request exact approval. Nothing installed."}
    store.save("runs", result["id"], result)
    result["report"] = str(write_report(store, result))
    return result


def run_due(store, current=None):
    current = current or datetime.now(timezone.utc)
    output = []
    with store.lock("scheduler"):
        config = preferences.load(store)
        for job in config["schedules"]:
            if not job["enabled"]:
                continue
            due = [t for t in slots(job, current) if timedelta(0) <= current - t <= timedelta(hours=1)]
            if not due:
                continue
            slot = max(due)
            key = digest([job, slot.isoformat()])[:24]
            if store.path("jobs", key).exists():
                continue
            record = {"id": key, "name": job["name"], "slot": slot.isoformat(), "status": "running", "at": now()}
            store.save("jobs", key, record)
            try:
                result = run(store, config, job["source"])
                record.update(status=result["status"], run_id=result["id"])
            except Exception:
                record.update(status="failed", error="Job failed; inspect configuration and retry manually")
            store.save("jobs", key, record)
            output.append(record)
    return output


def serve(store, interval=30):
    if not 10 <= interval <= 3600:
        raise ScoutError("Poll interval must be 10..3600 seconds")
    while True:
        run_due(store)
        time.sleep(interval)
