"""Pinned proposals, explicit approvals and reversible skill-folder installations."""
import os
import shutil
import tempfile
import hashlib
import zipfile
from pathlib import Path, PurePosixPath

from . import config as preferences
from .core import ScoutError, digest, identifier, now, skill_metadata, tree_hash
from .github import snapshot
from .inventory import assess, collect
from .security import scan


def source_skill(store, source_id, relative):
    root = store.root / "quarantine" / identifier(source_id)
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ScoutError("Unsafe skill path")
    result = root.joinpath(*path.parts)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ScoutError("Skill path escaped quarantine")
    return result


def subject(store, p):
    return store.root / "bundles" / identifier(p["id"]) / identifier(p["metadata"]["name"])


def fingerprint(p):
    return digest({k: p[k] for k in (
        "source_id", "revision", "source_hash", "skill_path", "content_hash", "metadata",
        "license_files", "security", "assessment", "target", "delivery", "destination", "previous_hash", "previous_record")})


def prepare(store, config, repo, skill=None, revision=None):
    source = snapshot(store, repo, revision=revision)
    root = store.root / "quarantine" / identifier(source["id"])
    manifests = sorted(p.relative_to(root).as_posix() for p in root.rglob("SKILL.md"))
    if skill is None:
        if len(manifests) != 1:
            return {"status": "selection_required" if manifests else "tool_only",
                    "source": source, "skills": manifests,
                    "next": "Select --skill relative/directory or review runtime integration manually. No scripts run."}
        skill = str(PurePosixPath(manifests[0]).parent)
    original = source_skill(store, source["id"], skill)
    metadata = skill_metadata(original / "SKILL.md")
    if original.name != metadata["name"] and skill != ".":
        raise ScoutError("Skill folder must match its declared name")
    delivery = config.get("delivery", "local")
    pid = digest([source["id"], skill, config["target"], delivery])[:24]
    if store.path("proposals", pid).exists():
        old = store.load("proposals", pid)
        if old["status"] == "installed":
            return old
        store.save("proposal-history", digest(old), old)
    p = {"id": pid, "source_id": source["id"], "skill_path": skill, "metadata": metadata}
    bundle = subject(store, p)
    if bundle.parent.exists():
        if bundle.parent.is_symlink():
            raise ScoutError("Invalid staging path")
        shutil.rmtree(bundle.parent)
    shutil.copytree(original, bundle)
    license_paths = [f.relative_to(root).as_posix() for f in root.rglob("*")
                     if f.is_file() and f.name.lower() in {"license", "license.md", "license.txt", "copying"}]
    for relative in license_paths:
        src = root / relative
        dest = bundle / "references" / "upstream-licenses" / (digest(relative)[:12] + "-" + src.name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
    target = config["target"]
    destination = preferences.default_skill_root(target) / metadata["name"] if delivery == "local" else None
    p.update(at=now(), repository=source["repository"], revision=source["revision"],
             source_hash=source["content_hash"], content_hash=tree_hash(bundle),
             license_files=license_paths, security={"source": scan(root), "bundle": scan(bundle)},
             assessment=assess(metadata, collect(config)), target=target, delivery=delivery,
             destination=str(destination) if destination else "ChatGPT Work supported skill installer",
             previous_hash=tree_hash(destination) if destination and destination.exists() else None,
             previous_record=store.load("installed", metadata["name"])
                 if store.path("installed", metadata["name"]).exists() else None,
             status="pending_review")
    p["fingerprint"] = fingerprint(p)
    store.save("proposals", pid, p)
    return p


def review(store, config, pid, decision, reason, evidence):
    if decision not in {"add", "update", "redundant", "conflict", "uncertain"}:
        raise ScoutError("Unsupported need-assessment decision")
    if len(reason.strip()) < 12 or len(evidence.strip()) < 12:
        raise ScoutError("Explain the marginal benefit and concrete evidence")
    p = store.load("proposals", pid)
    if p["status"] == "installed":
        raise ScoutError("Installed records are immutable; prepare a new version")
    p["assessment"].update(decision=decision, reason=reason[:4000], evidence=evidence[:8000],
                           inventory_fingerprint=collect(config)["fingerprint"], reviewed_at=now())
    p["status"] = "pending_approval"
    p.pop("approval", None)
    p["fingerprint"] = fingerprint(p)
    store.save("proposals", pid, p)
    return p


def validate(store, config, p):
    if p["fingerprint"] != fingerprint(p):
        raise ScoutError("Proposal changed; prepare and review again")
    bundle = subject(store, p)
    source = store.root / "quarantine" / identifier(p["source_id"])
    if tree_hash(source) != p["source_hash"] or tree_hash(bundle) != p["content_hash"]:
        raise ScoutError("Content changed after inspection; reacquire and rescan")
    for scope, expected in (("source", p["source_hash"]), ("bundle", p["content_hash"])):
        s = p["security"][scope]
        if s.get("status") != "eligible" or s.get("content_hash") != expected:
            raise ScoutError("Complete eligible source and bundle scans are required")
    if p["assessment"]["decision"] not in {"add", "update"}:
        raise ScoutError("A marginal-benefit assessment is required")
    if p["assessment"]["inventory_fingerprint"] != collect(config)["fingerprint"]:
        raise ScoutError("Existing setup changed; reassess")
    if p["target"] != config["target"]:
        raise ScoutError("Target agent changed")
    if p["delivery"] != config.get("delivery", "local"):
        raise ScoutError("Delivery method changed; prepare a new proposal")
    if p["delivery"] == "local":
        dest = preferences.default_skill_root(p["target"]) / p["metadata"]["name"]
        if p["destination"] != str(dest):
            raise ScoutError("Unexpected destination")
        if (tree_hash(dest) if dest.exists() else None) != p["previous_hash"]:
            raise ScoutError("Destination changed; preserve customizations and prepare again")
    elif p["delivery"] != "work" or p["destination"] != "ChatGPT Work supported skill installer":
        raise ScoutError("Unsupported delivery method")
    if not p["license_files"]:
        raise ScoutError("No upstream license found; automatic copying is unsupported")
    return bundle


def approve(store, config, pid, expected):
    p = store.load("proposals", pid)
    if p["status"] != "pending_approval" or expected != p["fingerprint"]:
        raise ScoutError("Approval must match a pending reviewed proposal")
    validate(store, config, p)
    p.update(approval={"fingerprint": expected, "at": now()}, status="approved")
    store.save("proposals", pid, p)
    return p


def install(store, config, pid):
    with store.lock("installation"):
        p = store.load("proposals", pid)
        if p["status"] != "approved" or p.get("approval", {}).get("fingerprint") != p["fingerprint"]:
            raise ScoutError("Explicit approval of this exact proposal is required")
        if p["delivery"] != "local":
            raise ScoutError("This proposal targets ChatGPT Work; export the approved package and use its supported installer")
        bundle = validate(store, config, p)
        dest = Path(p["destination"])
        if any(a.is_symlink() for a in [dest, *dest.parents]):
            raise ScoutError("Installation path contains a symbolic link")
        dest.parent.mkdir(parents=True, exist_ok=True)
        backup = store.root / "backups" / pid
        if backup.exists():
            raise ScoutError("A backup already exists")
        with tempfile.TemporaryDirectory(prefix=".skillscout-stage-", dir=dest.parent) as temp:
            stage = Path(temp) / dest.name
            shutil.copytree(bundle, stage)
            if tree_hash(stage) != p["content_hash"]:
                raise ScoutError("Staged content does not match inspection")
            previous = Path(temp) / "previous"
            if dest.exists():
                backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                shutil.copytree(dest, backup)
                if tree_hash(backup) != p["previous_hash"]:
                    raise ScoutError("Backup verification failed")
                os.replace(dest, previous)
            try:
                os.replace(stage, dest)
            except OSError:
                if previous.exists() and not dest.exists():
                    os.replace(previous, dest)
                raise
        p.update(status="installed", installed_at=now(), installed_hash=tree_hash(dest))
        store.save("proposals", pid, p)
        store.save("installed", p["metadata"]["name"], {
            "proposal_id": pid, "repository": p["repository"], "revision": p["revision"],
            "skill_path": p["skill_path"], "destination": str(dest)})
        return p


def rollback(store, pid):
    with store.lock("installation"):
        p = store.load("proposals", pid)
        if p["status"] != "installed" or fingerprint(p) != p["fingerprint"]:
            raise ScoutError("Only intact installation records can be rolled back")
        dest = preferences.default_skill_root(p["target"]) / p["metadata"]["name"]
        if str(dest) != p["destination"] or any(a.is_symlink() for a in [dest, *dest.parents]):
            raise ScoutError("Unsafe rollback destination")
        if tree_hash(dest) != p["content_hash"]:
            raise ScoutError("Installed files were edited; preserve them before rollback")
        backup = store.root / "backups" / identifier(pid)
        if p["previous_hash"] and (not backup.exists() or tree_hash(backup) != p["previous_hash"]):
            raise ScoutError("Backup changed or missing")
        with tempfile.TemporaryDirectory(prefix=".skillscout-rollback-", dir=dest.parent) as tmp:
            prior = Path(tmp) / "current"
            staged = Path(tmp) / "restored"
            if p["previous_hash"]:
                shutil.copytree(backup, staged)
            os.replace(dest, prior)
            try:
                if p["previous_hash"]:
                    os.replace(staged, dest)
            except OSError:
                os.replace(prior, dest)
                raise
        p.update(status="rolled_back", rolled_back_at=now())
        store.save("proposals", pid, p)
        if p.get("previous_record"):
            store.save("installed", p["metadata"]["name"], p["previous_record"])
        else:
            store.path("installed", p["metadata"]["name"]).unlink(missing_ok=True)
        return p


def export_work(store, config, pid, output):
    """Export approved exact bytes; do not claim to register a cloud skill."""
    with store.lock("installation"):
        p = store.load("proposals", pid)
        if (p["delivery"] != "work" or p["status"] not in {"approved", "exported"}
                or p.get("approval", {}).get("fingerprint") != p["fingerprint"]):
            raise ScoutError("Explicit approval of a Work-delivery proposal is required")
        bundle = validate(store, config, p)
        output = Path(output).expanduser().absolute()
        if output.suffix != ".zip" or output.exists() or any(a.is_symlink() for a in [output, *output.parents]):
            raise ScoutError("Choose a new non-linked .zip output path")
        if output.is_relative_to(store.root.absolute()):
            raise ScoutError("Export outside private state to avoid mixing evidence with deliverables")
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=output.parent, suffix=".zip")
        os.close(fd)
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as z:
                for path in sorted(bundle.rglob("*")):
                    if path.is_file():
                        z.write(path, p["metadata"]["name"] + "/" + path.relative_to(bundle).as_posix())
            if tree_hash(bundle) != p["content_hash"]:
                raise ScoutError("Bundle changed during export")
            os.replace(temp, output)
        finally:
            Path(temp).unlink(missing_ok=True)
        p.update(status="exported", exported_at=now(),
                 export_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
        store.save("proposals", pid, p)
        return {"proposal_id": pid, "path": str(output), "sha256": p["export_sha256"],
                "installed": False, "next": "Use ChatGPT Work's supported skill installer. This export is not account installation."}
