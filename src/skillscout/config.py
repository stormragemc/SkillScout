"""Explicit, private preferences. No account login or scheduler side effects."""
from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path

from .core import ScoutError, Store, read_json, write_json

CREATORS = ["nocode.joshua", "nick_saraev", "canwebuildthis", "byjoeym", "itsmariahbrunner"]
DEFAULTS = {
    "schema_version": 1,
    "interests": ["coding", "design"],
    "creators": CREATORS,
    "target": "codex",
    "delivery": "local",
    "instagram_enabled": False,
    "inventory_roots": [],
    "rules_files": [],
    "schedules": [],
    "budgets": {"candidates": 20, "posts_per_creator": 6, "model_input_chars": 16000, "model_calls": 3},
    "model": {"enabled": False, "name": "", "endpoint": "https://api.openai.com/v1/responses"},
}


def handle(value: str) -> str:
    value = value.lstrip("@").lower()
    if not re.fullmatch(r"[a-z0-9_][a-z0-9._]{0,29}", value):
        raise ScoutError("Invalid Instagram username")
    return value


def load(store: Store) -> dict:
    path = store.root / "config.json"
    if not path.exists():
        raise ScoutError("Run `skillscout init` first. It discloses the defaults without enabling scraping.")
    return read_json(path)


def save(store: Store, config: dict) -> None:
    write_json(store.root / "config.json", config)


def init(store: Store) -> dict:
    if not (store.root / "config.json").exists():
        save(store, deepcopy(DEFAULTS))
    # Never restore a removed creator during an upgrade or repeated initialization.
    return disclosure(load(store))


def disclosure(config: dict) -> dict:
    return {
        "preferences": config,
        "notice": "General means coding and design. The default Instagram sources are maintainer-selected "
                  "starting points, not endorsements or security certifications. Edit or disable them at any time. "
                  "No schedules, logins, model calls, or installations are enabled by init.",
        "instagram_sources": ["@" + c for c in config["creators"]],
        "approval": "New skills and updates require explicit, version-bound approval after inspection.",
    }


def default_skill_root(target: str) -> Path:
    if target not in ("codex", "claude", "gemini"):
        raise ScoutError("Target must be codex, claude, or gemini")
    return Path.home() / (".claude" if target == "claude" else ".agents") / "skills"

