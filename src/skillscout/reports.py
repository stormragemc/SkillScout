"""Escaped local reports; no external notifications or public uploads."""
import re
from .core import clean, identifier


def literal(value):
    text = clean(value, 16000).replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)


def write_report(store, report):
    lines = ["# SkillScout discovery report", "", "Time: " + literal(report["at"]), "",
             "Status: " + literal(report.get("status", "recorded")), "",
             "Candidates are untrusted. Popularity is not a security verdict.", ""]
    for result in report.get("results", [report]):
        lines += ["## " + literal(result.get("source", "source")), ""]
        for row in result.get("candidates", []):
            lines += ["- " + literal(row["repository"]) + ": " + literal(row["description"]),
                      "  Stars: " + str(row["stars"]) + "; ranking score: " + str(row["ranking"]["score"])]
        for post in result.get("new_posts", []):
            lines += ["- @" + literal(post["creator"]) + ": " + literal(post["url"]),
                      "  Caption only: " + literal(post["caption"])]
        for failure in result.get("failures", []):
            lines += ["- Access limitation: " + literal(failure)]
        lines += ["", literal(result.get("coverage", "")), ""]
    for failure in report.get("failures", []):
        lines += ["- Run limitation: " + literal(failure)]
    for entry in report.get("prepared_reviews", []):
        lines += ["- Review prepared: " + literal(entry)]
    for entry in report.get("updates", []):
        lines += ["- Update requires review: " + literal(entry)]
    lines += ["", "## Next step", "", literal(report.get("next", "Review before preparing an installation proposal.")), ""]
    path = store.root / "reports" / (identifier(report["id"]) + ".md")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o600)
    return path
