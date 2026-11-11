# Validation

The primary path is OpenAI ChatGPT Work / Codex. CI exercises the core on Ubuntu
and Windows with Python 3.11/3.12, builds the portable bundle, checks its extracted
runtime in temporary state, and builds the Python distribution.

## Automated coverage

- Defaults are disclosed and removed creators stay removed.
- Unsafe archive paths, links/collisions and unknown momentum cannot silently pass.
- Agent-Reach's current top-level items contract is covered with fixtures.
- Creator discovery requires explicit enablement and deduplicates post identities.
- Timezone schedules, weekly previews, DST gaps and once-per-slot claims are tested.
- Incomplete, suppressed and high-risk scanner reports cannot permit installation.
- Need review and exact approval precede local installation or Work export.
- Changed content/inventory/destination invalidates approval; user edits are preserved.
- Local installs and approved Work exports are distinct; exports claim no account installation.

## Live integration checks

A separate CI job installs the documented SkillSpector source revision and scans
a benign fixture and an inert malicious-instruction fixture. It never executes the
fixture instructions. A read-only GitHub check exercises public metadata, commit
resolution and optional historical signals.

The current run and exact tested SHA are visible in
[GitHub Actions](https://github.com/stormragemc/SkillScout/actions/workflows/ci.yml).
A successful fixture is not a security certification for SkillScout or any candidate.

## Not claimed as tested

- Instagram account login, live access to the default creators, and full video retrieval.
- Earshot/ffmpeg on each user's device; their adapters require installed tools.
- Paid OpenAI review against a live model; no user API key is supplied during development.
- Persistent account-level installation in ChatGPT Work.
- Live Claude Code/Gemini installation or publication in any universal directory.
- An unattended runner staying available on a user's machine.

These require the installing user's explicit setup. The maintainer's first-user
walkthrough is intentionally separate from developer fixtures.

## Recorded release-candidate check

[Run 42985904656](https://github.com/stormragemc/SkillScout/actions/runs/42985904656)
checked commit 4b845c6b49771f52507e86cff95151179bbe6943:

- 31 core tests passed on Ubuntu and Windows with Python 3.11 and 3.12.
- Two real SkillSpector tests passed in the separate integration job.
- The extracted portable runtime and Python package builds passed.
- Public GitHub metadata, commit resolution and historical star data returned successfully.
- No user accounts, Instagram sessions, persistent skill installs or paid model calls were activated.

Subsequent changes and their checks remain visible in the Actions history.
