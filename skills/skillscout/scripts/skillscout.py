#!/usr/bin/env python3
"""Portable entry point; importing does not initialize user state."""
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
runtime = here / "runtime"
if runtime.is_dir():
    sys.path.insert(0, str(runtime))
else:
    source = here.parents[2] / "src"
    if source.is_dir():
        sys.path.insert(0, str(source))
try:
    from skillscout.cli import main
except ImportError:
    raise SystemExit("Runtime missing. Build the portable bundle or install the CLI; read references/setup.md.")

if __name__ == "__main__":
    raise SystemExit(main())
