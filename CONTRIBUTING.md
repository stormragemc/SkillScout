# Contributing

Open an issue with a concrete use case or reproducible failure. Include OS,
Python/SkillScout versions, command, redacted error and a minimal public input.
Do not upload inventories, browser data, private reports or credentials.

Create a branch and keep changes focused. Describe the final behavior and relevant
validation. Keep popularity ranking separate from security policy. Tests should
exercise actual failure cases and trust boundaries.

```sh
python -m venv .venv
.venv/bin/python -m pip install -e . ruff build
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_bundle.py
.venv/bin/python scripts/check_package.py
```

Use .venv/Scripts executables on Windows. Use temporary state for every test.
Never enable accounts/schedules or install into a developer's real skill folders.
Label fixtures, live checks and untested paths. Keep SKILL.md concise and use its
references for details.
