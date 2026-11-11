"""Fail-closed SkillSpector adapter. No candidate code is executed."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .core import ScoutError, clean, now, tree_hash

PINNED_SPECTOR = "9dbf4fc75386169275e5f18c47686cb0d7274afa"


def command(args, timeout=180, cap=2_000_000):
    env = {k: v for k, v in os.environ.items() if k in {
        "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL", "VIRTUAL_ENV"}}
    env.update(PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1", DO_NOT_TRACK="1",
               LANGSMITH_TRACING="false", SEMGREP_SEND_METRICS="off")
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            result = subprocess.run(args, stdout=out, stderr=err, timeout=timeout,
                                    env=env, cwd=tempfile.gettempdir(), check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ScoutError("Integration executable failed or exceeded its time budget") from exc
        out.seek(0, 2)
        if out.tell() > cap:
            raise ScoutError("Integration output exceeded its byte budget")
        out.seek(0)
        return result.returncode, out.read(cap).decode("utf-8", errors="replace")


def gate(report, returncode):
    if not isinstance(report, dict):
        return {"status": "unverified", "reason": "Unsupported scanner report schema"}
    coverage = report.get("analysis_completeness", {})
    risk = report.get("risk_assessment", {})
    issues = report.get("issues")
    if not isinstance(coverage, dict) or not isinstance(risk, dict) or not isinstance(issues, list):
        return {"status": "unverified", "reason": "Unsupported scanner report schema"}
    complete = (report.get("execution_successful") is True and coverage.get("is_complete") is True
                and coverage.get("status") == "complete" and coverage.get("coverage_percent") == 100
                and not any(coverage.get(k) for k in
                            ("ledger_exceptions", "scope_exclusions", "limitations", "warnings"))
                and report.get("suppressed_count", 0) == 0 and not report.get("suppressed"))
    if not all(isinstance(i, dict) for i in issues):
        return {"status": "unverified", "reason": "Invalid finding records"}
    severities = [str(i.get("severity", "UNKNOWN")).upper() for i in issues]
    severities += [str(risk.get("max_issue_severity", "UNKNOWN")).upper(),
                   str(risk.get("severity", "UNKNOWN")).upper()]
    if any(s in {"HIGH", "CRITICAL"} for s in severities) or risk.get("recommendation") == "DO_NOT_INSTALL":
        return {"status": "blocked", "reason": "High/critical finding or do-not-install verdict"}
    if not complete or returncode != 0:
        return {"status": "unverified", "reason": "Required inspection failed, was suppressed, or was incomplete"}
    if any(s not in {"NONE", "LOW", "MEDIUM"} for s in severities):
        return {"status": "unverified", "reason": "Unknown severity in scanner output"}
    if "MEDIUM" in severities or risk.get("recommendation") != "SAFE":
        return {"status": "review_required", "reason": "Resolve findings and rescan"}
    return {"status": "eligible", "reason": "No blocking issues detected by complete configured static checks"}


def scan(bundle):
    fingerprint = tree_hash(bundle)
    binary = shutil.which("skillspector")
    base = {"at": now(), "content_hash": fingerprint, "engine": "SkillSpector", "mode": "static"}
    if not binary:
        return {**base, "status": "unverified", "reason": "SkillSpector is unavailable; installation is blocked"}
    try:
        _, version = command([binary, "--version"], timeout=30, cap=8000)
        with tempfile.TemporaryDirectory(prefix="skillscout-scan-") as d:
            output = Path(d) / "report.json"
            rc, _ = command([binary, "scan", str(bundle.resolve()), "--no-llm", "--fail-on-incomplete",
                             "--format", "json", "--output", str(output)], timeout=300)
            if output.is_symlink() or not output.is_file() or output.stat().st_size > 4_000_000:
                raise ScoutError("Scanner did not produce a bounded JSON report")
            report = json.loads(output.read_text(encoding="utf-8"))
        if tree_hash(bundle) != fingerprint:
            raise ScoutError("Bundle changed during inspection")
        return {**base, **gate(report, rc), "version": clean(version, 300), "report": report}
    except (ScoutError, ValueError, OSError) as exc:
        return {**base, "status": "unverified", "reason": clean(exc)}
