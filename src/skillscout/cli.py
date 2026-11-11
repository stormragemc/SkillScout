"""JSON CLI for host agents and terminal users. No implicit installs."""
import argparse
import json
import shutil
import sys
from pathlib import Path

from . import __version__, config, instagram, inventory, media, proposals, schedule
from .core import ScoutError, Store, clean


def parser():
    p = argparse.ArgumentParser(prog="skillscout", description="Discover, compare, inspect, approve, then install.")
    p.add_argument("--version", action="version", version="SkillScout " + __version__)
    p.add_argument("--home", type=Path, help="Private state directory, or SKILLSCOUT_HOME")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Show defaults without enabling accounts, schedules or models")
    pref = sub.add_parser("preferences")
    pref.add_argument("action", choices=["show", "set"])
    pref.add_argument("--interests", nargs="+")
    pref.add_argument("--target", choices=["codex", "claude", "gemini"])
    pref.add_argument("--delivery", choices=["local", "work"])
    for key in ("candidates", "posts-per-creator", "model-input-chars", "model-calls"):
        pref.add_argument("--" + key, type=int)
    creators = sub.add_parser("creators")
    creators.add_argument("action", choices=["list", "add", "remove", "explore"])
    creators.add_argument("handles", nargs="*")
    sub.add_parser("instagram").add_argument("action", choices=["enable", "disable"])
    inv = sub.add_parser("inventory")
    inv.add_argument("action", choices=["show", "add-root", "add-rules", "remove-root", "remove-rules"])
    inv.add_argument("path", nargs="?", type=Path)
    discover = sub.add_parser("discover")
    discover.add_argument("--source", choices=["github", "instagram", "all"], default="github")
    discover.add_argument("--limit", type=int, default=10)
    discover.add_argument("--rank", choices=["best-match", "popular", "new", "trending"], default="best-match")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("repository")
    inspect.add_argument("--skill", help="Relative skill directory containing SKILL.md")
    inspect.add_argument("--revision", help="Optional full commit SHA")
    rev = sub.add_parser("review")
    rev.add_argument("id")
    rev.add_argument("--decision", choices=["add", "update", "redundant", "conflict", "uncertain"])
    rev.add_argument("--reason")
    rev.add_argument("--evidence")
    rev.add_argument("--model", action="store_true")
    app = sub.add_parser("approve", help="Only after explicit user approval of the exact displayed proposal")
    app.add_argument("id")
    app.add_argument("--fingerprint", required=True)
    for name in ("install", "rollback", "show"):
        sub.add_parser(name).add_argument("id")
    export = sub.add_parser("export", help="Export approved content for ChatGPT Work installation")
    export.add_argument("id")
    export.add_argument("--output", required=True, type=Path)
    sub.add_parser("inbox")
    sub.add_parser("integrations")
    job = sub.add_parser("schedule")
    job.add_argument("action", choices=["list", "set", "pause", "resume", "remove", "run-due", "serve"])
    job.add_argument("name", nargs="?")
    job.add_argument("--source", choices=["github", "instagram", "all"], default="github")
    job.add_argument("--at", default="09:15")
    job.add_argument("--timezone", default="UTC")
    job.add_argument("--days", default="daily")
    job.add_argument("--poll", type=int, default=30)
    reel = sub.add_parser("reel")
    reel.add_argument("url")
    reel.add_argument("--creator")
    reel.add_argument("--explore", action="store_true")
    reel.add_argument("--watch", action="store_true")
    video = sub.add_parser("media")
    video.add_argument("path", type=Path)
    video.add_argument("--source", required=True)
    video.add_argument("--creator")
    video.add_argument("--transcript", type=Path)
    video.add_argument("--frames", action="store_true")
    video.add_argument("--audio", action="store_true")
    draft = sub.add_parser("draft")
    draft.add_argument("evidence_id")
    draft.add_argument("--name", required=True)
    draft.add_argument("--guidance-file", required=True, type=Path)
    model = sub.add_parser("model")
    model.add_argument("action", choices=["show", "configure", "disable"])
    model.add_argument("--name")
    model.add_argument("--allow-remote-review", action="store_true")
    return p


def execute(a, store):
    if a.command == "init":
        return config.init(store)
    if a.command == "integrations":
        return {"tools": {n: bool(shutil.which(n)) for n in ("skillspector", "agent-reach", "earshot", "ffmpeg")},
                "notice": "Presence is not a live test. No dependencies installed or sessions accessed."}
    c = config.load(store)
    if a.command == "preferences":
        if a.action == "set":
            if a.interests:
                c["interests"] = [clean(i, 100) for i in a.interests[:10]]
            if a.target:
                c["target"] = a.target
            if a.delivery:
                c["delivery"] = a.delivery
            for key, cap in (("candidates", 50), ("posts_per_creator", 20), ("model_input_chars", 32000), ("model_calls", 5)):
                value = getattr(a, key)
                if value is not None:
                    if not 1 <= value <= cap:
                        raise ScoutError(f"{key} must be 1..{cap}")
                    c["budgets"][key] = value
            config.save(store, c)
        return config.disclosure(c)
    if a.command == "creators":
        names = [config.handle(h) for h in a.handles]
        if a.action == "explore":
            if len(names) != 1:
                raise ScoutError("Specify one creator for one-time exploration")
            return instagram.discover(store, c, names[0])
        if a.action in {"add", "remove"}:
            if not names:
                raise ScoutError("Provide a creator")
            for name in names:
                if a.action == "add" and name not in c["creators"]:
                    c["creators"].append(name)
                elif a.action == "remove" and name in c["creators"]:
                    c["creators"].remove(name)
            config.save(store, c)
        return {"creators": ["@" + n for n in c["creators"]], "instagram_enabled": c.get("instagram_enabled", False)}
    if a.command == "instagram":
        c["instagram_enabled"] = a.action == "enable"
        config.save(store, c)
        return {"enabled": c["instagram_enabled"], "notice": "Agent-Reach may use its configured browser session. "
                "Manage accounts in Agent-Reach. SkillScout never imports or exports cookies."}
    if a.command == "inventory":
        if a.action != "show":
            if not a.path:
                raise ScoutError("Specify an exact skills directory or rules file")
            if a.path.expanduser().is_symlink():
                raise ScoutError("Inventory registration cannot use a symlink")
            path = a.path.expanduser().resolve()
            key = "inventory_roots" if a.action.endswith("root") else "rules_files"
            if a.action.startswith("remove"):
                if str(path) in c[key]:
                    c[key].remove(str(path))
            else:
                if (key == "inventory_roots" and not path.is_dir()) or (key == "rules_files" and not path.is_file()):
                    raise ScoutError("Inventory path missing or wrong type")
                if str(path) not in c[key]:
                    c[key].append(str(path))
            config.save(store, c)
        return inventory.collect(c)
    if a.command == "discover":
        c["budgets"]["candidates"] = min(max(1, a.limit), c["budgets"]["candidates"])
        return schedule.run(store, c, a.source, mode=a.rank)
    if a.command == "inspect":
        return proposals.prepare(store, c, a.repository, a.skill, a.revision)
    if a.command == "review":
        if a.model:
            from .reviewer import model_review
            return model_review(store, c, a.id)
        if not (a.decision and a.reason and a.evidence):
            raise ScoutError("Provide --decision, --reason and --evidence, or explicitly use --model")
        return proposals.review(store, c, a.id, a.decision, a.reason, a.evidence)
    if a.command == "approve":
        return proposals.approve(store, c, a.id, a.fingerprint)
    if a.command == "export":
        return proposals.export_work(store, c, a.id, a.output)
    if a.command == "install":
        return proposals.install(store, c, a.id)
    if a.command == "rollback":
        return proposals.rollback(store, a.id)
    if a.command == "show":
        return store.load("proposals", a.id)
    if a.command == "inbox":
        return {"proposals": [{k: p.get(k) for k in ("id", "repository", "status", "fingerprint", "assessment")}
                              for p in store.list("proposals")],
                "runs": [{k: r.get(k) for k in ("id", "at", "source", "status")} for r in store.list("runs")[-20:]],
                "reports_directory": str(store.root / "reports")}
    if a.command == "schedule":
        if a.action == "run-due":
            return {"jobs": schedule.run_due(store)}
        if a.action == "serve":
            schedule.serve(store, a.poll)
        if a.action != "list":
            if not a.name:
                raise ScoutError("Specify schedule name")
            existing = next((j for j in c["schedules"] if j["name"] == a.name), None)
            if a.action == "set":
                new = schedule.make(a.name, a.source, a.at, a.timezone, a.days)
                c["schedules"] = [j for j in c["schedules"] if j["name"] != a.name] + [new]
            elif not existing:
                raise ScoutError("Schedule not found")
            elif a.action == "remove":
                c["schedules"].remove(existing)
            else:
                existing["enabled"] = a.action == "resume"
            config.save(store, c)
        return {"schedules": [{**j, "next_runs": schedule.upcoming(j) if j["enabled"] else []} for j in c["schedules"]],
                "runner": "Run schedule serve on an available machine, or call run-due from an OS scheduler. "
                          "Saving a schedule does not start a process."}
    if a.command == "reel":
        result = {"url": instagram.reel_identity(a.url), "creator": config.handle(a.creator),
                  "method": "user_or_host_supplied"} if a.creator else instagram.resolve_creator(a.url)
        creator = result.get("creator")
        if (a.watch or a.explore) and not creator:
            raise ScoutError("Posting account unresolved; use an authorized browser before supplying --creator")
        if a.watch:
            if creator not in c["creators"]:
                c["creators"].append(creator)
                config.save(store, c)
            result["watching"] = True
        if a.explore:
            result["exploration"] = instagram.discover(store, c, creator)
        result["offer"] = "Explore this creator once, or add them to future checks? These are separate choices."
        return result
    if a.command == "media":
        return media.analyze(store, a.path, a.source, a.creator, a.transcript, a.frames, a.audio)
    if a.command == "draft":
        if a.guidance_file.is_symlink() or a.guidance_file.stat().st_size > 16000:
            raise ScoutError("Guidance must be a non-linked text file under 16 KB")
        return media.draft(store, a.evidence_id, a.name, a.guidance_file.read_text(encoding="utf-8"))
    if a.command == "model":
        if a.action == "disable":
            c["model"]["enabled"] = False
        if a.action == "configure":
            if not a.name or not a.allow_remote_review:
                raise ScoutError("Specify --name and --allow-remote-review after reviewing data disclosure")
            c["model"].update(name=clean(a.name, 100), enabled=True, allow_remote_review=True)
        config.save(store, c)
        return {"model": c["model"], "disclosure": "When enabled, bounded candidate text and setup summaries are sent "
                "to OpenAI using the runner's OPENAI_API_KEY. Model review never approves or installs. "
                "Usage limits are not a currency-denominated cost guarantee."}
    raise ScoutError("Unknown command")


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        result = execute(a, Store(a.home))
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=True, indent=2))
        return 0
    except (ScoutError, OSError, ValueError) as exc:
        message = clean(exc) if isinstance(exc, ScoutError) else "File, network or configuration operation failed"
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=True), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
