"""Bounded, authenticated GitHub API reads and explainable discovery."""
from __future__ import annotations

import io
import json
import math
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

from .core import ScoutError, Store, clean, digest, now, tree_hash

HOSTS = {"api.github.com", "codeload.github.com", "github.com", "raw.githubusercontent.com"}
TERMS = {
    "coding": "coding code developer programming testing debugging automation agent workflow python javascript",
    "design": "design frontend interface ui ux accessibility typography animation motion css react",
}


def repository(value: str) -> str:
    if value.startswith("https://"):
        u = urllib.parse.urlsplit(value)
        if u.hostname != "github.com" or u.username or u.password or u.port not in (None, 443):
            raise ScoutError("Use a github.com repository URL or owner/repo")
        value = u.path.strip("/")
    value = value.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", value):
        raise ScoutError("Expected owner/repo; submit a repository root URL")
    if value.split("/")[1] in {".", ".."}:
        raise ScoutError("Invalid repository name")
    return value


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        if u.scheme != "https" or u.hostname not in HOSTS or u.username or u.port not in (None, 443):
            raise ScoutError("GitHub redirected outside the allowed HTTPS hosts")
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        if result and u.hostname != urllib.parse.urlsplit(req.full_url).hostname:
            result.remove_header("Authorization")
        return result


class GitHub:
    def __init__(self):
        self.opener = urllib.request.build_opener(SafeRedirect())
        self.requests = 0

    def request(self, path: str, *, binary=False, cap=4_000_000):
        self.requests += 1
        if self.requests > 100:
            raise ScoutError("Per-run GitHub request budget reached")
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "SkillScout/0.1.0"}
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request("https://api.github.com" + path, headers=headers)
        try:
            with self.opener.open(req, timeout=30) as response:
                raw = response.read(cap + 1)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                raise ScoutError("GitHub access/rate limit reached; wait for its retry/reset window") from exc
            raise ScoutError(f"GitHub returned HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ScoutError("GitHub request failed; check network access") from exc
        if len(raw) > cap:
            raise ScoutError("GitHub response exceeded the supported byte limit")
        try:
            return raw if binary else json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise ScoutError("GitHub returned invalid JSON") from exc

    def metadata(self, repo: str) -> dict:
        return self.request("/repos/" + repository(repo))

    def revision(self, repo: str) -> str:
        # HEAD resolves the default branch; a response is always pinned before acquisition.
        value = self.request("/repos/" + repository(repo) + "/commits/HEAD")["sha"]
        if not re.fullmatch(r"[a-f0-9]{40}", value):
            raise ScoutError("Invalid commit identity returned by GitHub")
        return value

    def history(self, repo: str) -> dict:
        try:
            rows = self.request("/repos/" + repository(repo) + "/stargazers/history?per_page=3")
            if not isinstance(rows, list):
                raise ValueError()
            days = {}
            for row in rows:
                start = datetime.fromtimestamp(row["week"], timezone.utc).date()
                if len(row["days"]) != 7:
                    raise ValueError()
                for i, count in enumerate(row["days"]):
                    if type(count) is not int or count < 0:
                        raise ValueError()
                    day = start + timedelta(days=i)
                    if day < datetime.now(timezone.utc).date():
                        days[day] = count
            today = datetime.now(timezone.utc).date()
            recent_keys = [today - timedelta(days=i) for i in range(1, 4)]
            baseline_keys = [today - timedelta(days=i) for i in range(4, 11)]
            if not all(k in days for k in recent_keys + baseline_keys):
                return {"available": False, "reason": "Insufficient complete historical days"}
            recent = sum(days[k] for k in recent_keys) / 3
            previous = sum(days[k] for k in baseline_keys) / 7
            return {"available": True, "stars_per_day": round(recent, 3),
                    "previous_per_day": round(previous, 3),
                    "acceleration": round(recent / max(previous, 5), 3),
                    "note": "Daily star creations, not net growth; provider day boundaries may differ from UTC."}
        except (ScoutError, ValueError, KeyError, TypeError, OverflowError):
            return {"available": False, "reason": "History unavailable; momentum remains unknown"}


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def relevance(text: str, interests: list[str]) -> float:
    wanted = tokens(" ".join(TERMS.get(i.lower(), i) for i in interests))
    return min(1.0, len(tokens(text) & wanted) / max(1, min(8, len(wanted))))


def rank(meta: dict, history: dict, interests: list[str]) -> dict:
    text = " ".join([meta.get("name", ""), meta.get("description") or "", " ".join(meta.get("topics", []))])
    r = relevance(text, interests)
    stars = max(0, int(meta.get("stargazers_count", 0)))
    popularity = min(1, math.log1p(stars) / math.log1p(100000))
    components = {"relevance": r, "popularity": popularity}
    weights = {"relevance": .65, "popularity": .35}
    if history.get("available"):
        speed = history["stars_per_day"]
        acceleration = history["acceleration"]
        components["momentum"] = .7 * min(1, math.log1p(speed) / math.log1p(500)) + .3 * min(1, acceleration / 10)
        weights = {"relevance": .45, "popularity": .15, "momentum": .4}
    emerging = bool(history.get("available") and stars < 5000 and
                    history["stars_per_day"] >= 10 and history["acceleration"] >= 2)
    return {"score": round(100 * sum(components[k] * weights[k] for k in weights), 2),
            "components": components, "weights": weights, "emerging": emerging,
            "algorithm": "topic-match-v1", "note": "Discovery heuristic; not a quality or security rating"}


def discover(store: Store, config: dict, limit: int = 10, client: GitHub | None = None,
             mode: str = "best-match") -> dict:
    client = client or GitHub()
    limit = max(1, min(limit, config["budgets"]["candidates"], 50))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    queries = ["topic:agent-skills archived:false", '"agent skills" in:readme archived:false',
               f"topic:claude-code created:>={cutoff} archived:false"]
    candidates, incomplete = {}, []
    for query in queries:
        result = client.request("/search/repositories?" + urllib.parse.urlencode(
            {"q": query, "sort": "updated" if "created:" in query else "stars", "per_page": limit}))
        if result.get("incomplete_results"):
            incomplete.append(query)
        for item in result.get("items", []):
            candidates[item["id"]] = item
    rows = []
    for meta in list(candidates.values())[:limit]:
        repo = repository(meta["full_name"])
        history = client.history(repo)
        ranking = rank(meta, history, config["interests"])
        rows.append({"repository": repo, "url": "https://github.com/" + repo,
                     "description": clean(meta.get("description") or ""),
                     "stars": meta.get("stargazers_count", 0), "created_at": meta.get("created_at"),
                     "history": history, "ranking": ranking, "status": "discovered"})
    key = {"popular": lambda r: r["stars"], "new": lambda r: r["created_at"] or "",
           "trending": lambda r: r["ranking"]["components"].get("momentum", -1),
           "best-match": lambda r: r["ranking"]["score"]}[mode]
    rows.sort(key=key, reverse=True)
    report = {"id": "github-" + digest([now(), rows])[:16], "at": now(), "source": "github",
              "candidates": rows, "search_incomplete": incomplete,
              "coverage": "Configured queries and bounded results; not all of GitHub"}
    store.save("runs", report["id"], report)
    return report


def extract_archive(raw: bytes, destination: Path) -> None:
    """Reject traversal, links, special files, collisions and resource bombs."""
    if destination.exists():
        raise ScoutError("Snapshot destination already exists")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > 5000:
                raise ScoutError("Unsupported archive size")
            planned, seen, total = [], set(), 0
            prefix = entries[0].filename.split("/")[0]
            for entry in entries:
                parts = PurePosixPath(entry.filename).parts
                mode = (entry.external_attr >> 16) & 0o170000
                if not parts or parts[0] != prefix or ".." in parts or "\\" in entry.filename:
                    raise ScoutError("Unsafe archive path")
                if PurePosixPath(entry.filename).is_absolute() or mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ScoutError("Links or special archive entries are unsupported")
                if len(parts) == 1:
                    continue
                relative = PurePosixPath(*parts[1:])
                if any(":" in p or p.endswith((".", " ")) or p.upper().split(".")[0] in
                       {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                        *(f"LPT{i}" for i in range(1, 10))} for p in relative.parts):
                    raise ScoutError("Nonportable archive filename")
                key = str(relative).casefold()
                if key in seen:
                    raise ScoutError("Duplicate archive path")
                seen.add(key)
                total += entry.file_size
                if entry.file_size > 4_000_000 or total > 32_000_000:
                    raise ScoutError("Archive exceeds inspection byte limits")
                if entry.file_size / max(entry.compress_size, 1) > 200:
                    raise ScoutError("Archive expansion limit exceeded")
                planned.append((entry, relative))
            destination.mkdir(parents=True, mode=0o700)
            for entry, relative in planned:
                target = destination.joinpath(*relative.parts)
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(entry) as source:
                        data = source.read(4_000_001)
                    if len(data) != entry.file_size:
                        raise ScoutError("Archive member size mismatch")
                    target.write_bytes(data)
    except (zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        raise ScoutError("Invalid or encrypted GitHub archive") from exc


def snapshot(store: Store, repo: str, client: GitHub | None = None) -> dict:
    client = client or GitHub()
    repo = repository(repo)
    revision = client.revision(repo)
    sid = digest([repo.lower(), revision])[:24]
    destination = store.root / "quarantine" / sid
    record_path = store.path("sources", sid)
    if record_path.exists():
        record = store.load("sources", sid)
        if tree_hash(destination) != record["content_hash"]:
            raise ScoutError("Stored snapshot changed; remove it and reacquire")
        return record
    if destination.exists():
        raise ScoutError("Incomplete prior acquisition; remove its quarantine directory before retrying")
    raw = client.request(f"/repos/{repo}/zipball/{revision}", binary=True, cap=32_000_000)
    extract_archive(raw, destination)
    record = {"id": sid, "repository": repo, "revision": revision,
              "content_hash": tree_hash(destination), "at": now(), "path": str(destination)}
    store.save("sources", sid, record)
    return record

