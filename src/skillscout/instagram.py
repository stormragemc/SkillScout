"""Creator-scoped metadata through an explicitly enabled Agent-Reach session."""
import html
import json
import re
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from .config import handle
from .core import ScoutError, clean, digest, now
from .github import relevance, repository
from .security import command


def reel_identity(url):
    u = urllib.parse.urlsplit(url)
    if (u.scheme != "https" or u.hostname not in {"instagram.com", "www.instagram.com"}
            or u.username or u.password or u.port not in (None, 443)):
        raise ScoutError("Use an HTTPS instagram.com reel or post URL")
    m = re.fullmatch(r"/(?:reel|reels|p)/([A-Za-z0-9_-]{3,100})/?", u.path)
    if not m:
        raise ScoutError("Unsupported Instagram post URL")
    return "https://www.instagram.com/reel/" + m[1] + "/"


def repo_links(text):
    found = []
    for link in re.findall(r"https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", text):
        try:
            repo = repository(link.rstrip(".,"))
            if repo not in found:
                found.append(repo)
        except ScoutError:
            pass
    return found


def reach_posts(username, limit):
    binary = shutil.which("agent-reach")
    if not binary:
        raise ScoutError("NEED_SETUP: Agent-Reach unavailable; no software or sessions were configured")
    rc, raw = command([binary, "instagram", "posts", handle(username), "--limit", str(limit),
                       "--timeout", "45"], timeout=60)
    try:
        envelope = json.loads(raw)
    except ValueError as exc:
        raise ScoutError("UPSTREAM_BROKEN: Invalid Agent-Reach JSON") from exc
    if not isinstance(envelope, dict):
        raise ScoutError("Unsupported Agent-Reach envelope")
    if rc or envelope.get("ok") is not True:
        code = (envelope.get("error") or {}).get("code", "UPSTREAM_BROKEN")
        raise ScoutError(clean(code, 60) + ": Check Agent-Reach status/login locally; no automatic retry")
    # Current unified actions return top-level items; management commands use result.
    items = envelope.get("items")
    if items is None:
        result = envelope.get("result")
        items = result if isinstance(result, list) else (result or {}).get("items")
    if not isinstance(items, list):
        raise ScoutError("Unsupported Agent-Reach result schema")
    return items[:limit]


def normalize(item, creator):
    raw_url = item.get("url") or item.get("permalink") or item.get("link")
    if not raw_url:
        code = item.get("shortcode") or item.get("code")
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,100}", code):
            return None
        raw_url = "https://www.instagram.com/reel/" + code + "/"
    try:
        url = reel_identity(str(raw_url))
    except ScoutError:
        return None
    caption = item.get("caption") or item.get("text") or item.get("description") or item.get("content") or ""
    if isinstance(caption, dict):
        caption = caption.get("text", "")
    text = clean(caption, 16000)
    return {"id": digest(url)[:24], "url": url, "creator": handle(creator), "caption": text,
            "published_at": clean(item.get("published_at") or item.get("timestamp") or "", 100),
            "views": item.get("view_count") if type(item.get("view_count")) is int else None,
            "github_candidates": repo_links(text), "evidence_level": "caption_only",
            "claims_verified": False, "seen_at": now()}


def discover(store, config, creator=None):
    if not config.get("instagram_enabled", False):
        raise ScoutError("Instagram disabled. Enable explicitly after reviewing configured browser session use.")
    creators = [handle(creator)] if creator else config["creators"]
    new, seen, failures = [], [], []
    for username in creators:
        try:
            items = reach_posts(username, min(20, config["budgets"]["posts_per_creator"]))
            for item in items:
                post = normalize(item, username) if isinstance(item, dict) else None
                if post is None:
                    failures.append({"creator": username, "status": "UNSUPPORTED_POST_RECORD"})
                    continue
                post["relevance"] = relevance(post["caption"], config["interests"])
                exists = store.path("posts", post["id"]).exists()
                previous = store.load("posts", post["id"]) if exists else {}
                post["first_seen_at"] = previous.get("first_seen_at", post["seen_at"])
                store.save("posts", post["id"], post)
                (seen if exists else new).append(post)
        except ScoutError as exc:
            failures.append({"creator": username, "status": clean(exc)})
    coverage = {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    for post in store.list("posts"):
        try:
            if datetime.fromisoformat(post.get("first_seen_at", post["seen_at"])) < cutoff:
                continue
        except (ValueError, KeyError):
            continue
        for repo in post.get("github_candidates", []):
            coverage.setdefault(repo, set()).add(post["creator"])
    report = {"id": "instagram-" + digest([now(), creators])[:16], "at": now(), "source": "instagram",
              "new_posts": new, "previously_seen": len(seen), "failures": failures,
              "creator_mentions": {r: sorted(c) for r, c in coverage.items()},
              "coverage": "Bounded observed creator posts, not all Instagram. Caption-only evidence is not a watched video."}
    store.save("runs", report["id"], report)
    return report


class InstagramRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        if (u.scheme != "https" or u.hostname not in {"www.instagram.com", "instagram.com"}
                or u.username or u.port not in (None, 443)):
            raise ScoutError("Instagram redirected outside its allowed public website")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def resolve_creator(url):
    url = reel_identity(url)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SkillScout/0.1.0"})
        with urllib.request.build_opener(InstagramRedirect()).open(req, timeout=20) as response:
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ScoutError("Public metadata exceeds limits")
        text = raw.decode("utf-8", errors="replace")
        for script in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.S):
            try:
                data = json.loads(html.unescape(script))
            except ValueError:
                continue
            for record in data if isinstance(data, list) else [data]:
                author = record.get("author") if isinstance(record, dict) else None
                if isinstance(author, list):
                    author = author[0] if len(author) == 1 else None
                u = urllib.parse.urlsplit(author.get("url", "") if isinstance(author, dict) else "")
                if u.hostname in {"www.instagram.com", "instagram.com"}:
                    return {"url": url, "creator": handle(u.path.strip("/")),
                            "method": "public_structured_author",
                            "offer": "Explore this creator once, or add them to the watchlist?"}
    except (OSError, ScoutError, ValueError):
        pass
    return {"url": url, "creator": None, "status": "unresolved",
            "next": "Inspect the posting account with an authorized browser/connector, then supply --creator. Do not guess."}
