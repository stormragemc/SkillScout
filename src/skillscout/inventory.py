"""An explicit capability inventory; no reading browser sessions or chat history."""
from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

from .core import ScoutError, Store, clean, digest, skill_metadata
from .github import tokens


def collect(config: dict) -> dict:
    entries, warnings = [], []
    for raw in config["inventory_roots"]:
        root = Path(raw).expanduser()
        if root.is_symlink() or not root.is_dir():
            warnings.append("Inventory root unavailable: " + str(root))
            continue
        # Exactly one skill directory level; never crawl the user's home directory.
        for skill in sorted(root.iterdir())[:2000]:
            if not skill.is_dir() or skill.is_symlink():
                continue
            path = skill / "SKILL.md"
            if not path.exists():
                continue
            try:
                meta = skill_metadata(path)
                entries.append({**meta, "path": str(path), "hash": digest(path.read_text(encoding="utf-8")),
                                "kind": "skill"})
            except (ScoutError, OSError, UnicodeError) as exc:
                warnings.append(f"{path.name}: {clean(exc)}")
    for raw in config["rules_files"]:
        path = Path(raw).expanduser()
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 64_000:
            warnings.append("Rules file unavailable or oversized: " + str(path))
            continue
        text = path.read_text(encoding="utf-8")
        entries.append({"name": path.name, "description": clean(text, 4000), "hash": digest(text),
                        "kind": "rules", "path": str(path), "estimated_tokens": (len(text) + 3) // 4})
    return {"entries": entries, "warnings": warnings, "fingerprint": digest([entries, warnings]),
            "scope": "Explicit roots and rules files only; unexposed chat memories are unknown"}


def bm25(query: str, documents: list[str]) -> list[float]:
    """Small corpus BM25, used to shortlist overlaps rather than certify redundancy."""
    docs = [list(__import__("re").findall(r"[a-z0-9]+", d.lower())) for d in documents]
    average = sum(map(len, docs)) / max(1, len(docs)) or 1
    scores = []
    for doc in docs:
        counts = Counter(doc)
        score = 0.0
        for term in tokens(query):
            frequency = sum(term in other for other in docs)
            idf = math.log(1 + (len(docs) - frequency + .5) / (frequency + .5))
            tf = counts[term]
            score += idf * tf * 2.2 / (tf + 1.2 * (.25 + .75 * len(doc) / average)) if tf else 0
        scores.append(score)
    return scores


def assess(metadata: dict, inventory: dict) -> dict:
    documents = [e["name"] + " " + e["description"] for e in inventory["entries"]]
    scores = bm25(metadata["name"] + " " + metadata["description"], documents)
    overlap = sorted([{ "name": e["name"], "path": e["path"], "score": round(s, 3)}
                      for e, s in zip(inventory["entries"], scores) if s > 0],
                     key=lambda x: x["score"], reverse=True)[:5]
    same_name = any(e["name"] == metadata["name"] for e in inventory["entries"])
    return {"decision": "uncertain", "reason": "A bounded capability review is required before approval.",
            "possible_update": same_name, "overlap_shortlist": overlap,
            "inventory_fingerprint": inventory["fingerprint"],
            "estimated_loaded_tokens": metadata["estimated_tokens"],
            "estimated_discovery_tokens": (len(metadata["name"] + metadata["description"]) + 3) // 4,
            "estimate_note": "Character-based estimates, not model tokenizer measurements. References load on demand."}

