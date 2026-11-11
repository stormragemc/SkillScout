"""Bounded local storage, content identities, and shared validation."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ScoutError(Exception):
    """A failure that can be shown without disclosing credentials."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def clean(value: Any, limit: int = 4000) -> str:
    # Untrusted strings must not control terminals, Markdown structure or logs.
    return " ".join("".join(c for c in str(value) if c.isprintable() or c.isspace()).split())[:limit]


def read_json(path: Path, limit: int = 4_000_000) -> Any:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ScoutError(f"Missing, linked, or oversized JSON file: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ScoutError(f"Invalid JSON: {path.name}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise ScoutError("Refusing to overwrite a symbolic link")
    fd, temp = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=True, indent=2)
            output.write("\n")
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def tree_hash(root: Path) -> str:
    if root.is_symlink() or not root.is_dir():
        raise ScoutError("Bundle must be a real directory")
    entries = []
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ScoutError("Symbolic links are not supported in installable bundles")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ScoutError("Special files are not supported")
        total += path.stat().st_size
        if len(entries) >= 5000 or total > 32_000_000 or path.stat().st_size > 4_000_000:
            raise ScoutError("Bundle exceeds supported inspection limits")
        entries.append([path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()])
    if not entries:
        raise ScoutError("Empty bundle")
    return digest(entries)


def identifier(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,100}", value) or value in {".", ".."}:
        raise ScoutError("Invalid identifier")
    return value


def skill_metadata(path: Path) -> dict:
    """Read the portable name/description subset without executing a YAML loader.

    Complex YAML is intentionally rejected; inspection tools can support more formats.
    """
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64_000:
        raise ScoutError("Missing, linked, or oversized SKILL.md")
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        raise ScoutError("SKILL.md needs YAML frontmatter")
    fields = {}
    lines = match[1].splitlines()
    for key in ("name", "description"):
        for i, line in enumerate(lines):
            if not line.startswith(key + ":"):
                continue
            value = line.partition(":")[2].strip()
            if value in (">", ">-", "|", "|-"):
                continuation = []
                for following in lines[i + 1:]:
                    if following and not following[0].isspace():
                        break
                    continuation.append(following.strip())
                value = " ".join(continuation)
            elif value.startswith('"'):
                try:
                    value = json.loads(value)
                except ValueError as exc:
                    raise ScoutError("Unsupported quoted frontmatter") from exc
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            if not isinstance(value, str):
                raise ScoutError("Skill metadata must be text")
            fields[key] = value
            break
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields.get("name", "")):
        raise ScoutError("Skill name must use lowercase words separated by single hyphens")
    if len(fields["name"]) > 64 or not 1 <= len(fields.get("description", "")) <= 1024:
        raise ScoutError("Unsupported skill metadata lengths")
    return {**fields, "estimated_tokens": (len(text) + 3) // 4}


class Store:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root or os.environ.get("SKILLSCOUT_HOME") or Path.home() / ".skillscout").expanduser()
        if self.root.is_symlink():
            raise ScoutError("State directory cannot be a symbolic link")

    def path(self, category: str, item: str) -> Path:
        return self.root / identifier(category) / (identifier(item) + ".json")

    def save(self, category: str, item: str, value: Any) -> None:
        write_json(self.path(category, item), value)

    def load(self, category: str, item: str) -> Any:
        return read_json(self.path(category, item))

    def list(self, category: str) -> list:
        return [read_json(p) for p in sorted((self.root / identifier(category)).glob("*.json"))]

    @contextlib.contextmanager
    def lock(self, name: str):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.root / (identifier(name) + ".lock")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise ScoutError(f"Another {name} operation is running; inspect {path} if a process crashed") from exc
        try:
            with os.fdopen(fd, "w") as output:
                output.write(str(os.getpid()))
            yield
        finally:
            path.unlink(missing_ok=True)

