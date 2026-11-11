#!/usr/bin/env python3
"""Check manifests and extracted runtime without account installation."""
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skillscout.core import skill_metadata


def check():
    for name in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json",
                 ".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "gemini-extension.json"):
        assert json.loads((ROOT / name).read_text())["name"] == "skillscout"
    skill = ROOT / "skills/skillscout"
    assert skill_metadata(skill / "SKILL.md")["name"] == "skillscout"
    for name in ("setup", "commands", "integrations", "security", "scheduling"):
        assert (skill / "references" / (name + ".md")).is_file()
    with tempfile.TemporaryDirectory() as d:
        with zipfile.ZipFile(ROOT / "dist/skillscout.zip") as z:
            assert all(p.startswith("skillscout/") and ".." not in Path(p).parts for p in z.namelist())
            z.extractall(d)
        script = Path(d) / "skillscout/scripts/skillscout.py"
        out = subprocess.check_output([sys.executable, str(script), "--home", str(Path(d) / "state"), "init"], text=True)
        result = json.loads(out)["result"]
        assert result["preferences"]["interests"] == ["coding", "design"]
        assert result["preferences"]["schedules"] == []
        assert len(result["instagram_sources"]) == 5
    print("Manifests and extracted portable runtime passed; no account installation performed.")


if __name__ == "__main__":
    check()
