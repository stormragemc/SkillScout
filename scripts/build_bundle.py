#!/usr/bin/env python3
"""Build a reproducible standalone skill ZIP without installing it."""
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        skill = Path(d) / "skillscout"
        shutil.copytree(ROOT / "skills/skillscout", skill,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(ROOT / "src/skillscout", skill / "scripts/runtime/skillscout",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "LICENSE", skill / "LICENSE")
        target = output / "skillscout.zip"
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for path in sorted(skill.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo(path.relative_to(Path(d)).as_posix(), (2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    z.writestr(info, path.read_bytes())
        checksum = hashlib.sha256(target.read_bytes()).hexdigest()
        (output / "SHA256SUMS").write_text(checksum + "  skillscout.zip\n", encoding="utf-8")
    print(json.dumps({"bundle": str(target), "sha256": checksum, "installed": False}))
    return target


if __name__ == "__main__":
    build()
