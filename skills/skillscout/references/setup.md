# Setup

Require Python 3.11+. Use the full checkout or the self-contained bundle built by
`python scripts/build_bundle.py`. A copied SKILL.md is not an installed runtime.

The CLI can be installed in a dedicated environment with
`uv tool install git+https://github.com/stormragemc/SkillScout.git` after the user
reviews it. Follow the README for Windows and virtual-environment alternatives.

For candidate installs in Work select `preferences set --delivery work`, then
export an approved proposal. The host performs account installation and versioning.

ChatGPT Work needs a Python/file executor and its supported skill installation
flow. Local Codex can use the same skill and CLI. Plain chat without execution
cannot run the tools. The repository's local plugin marketplace is a distribution
option for compatible clients, not a public-directory listing or hosted MCP service.

Run `integrations` to check executable presence. It does not test account access.
Enable no accounts, schedules or models by default. Optional integrations require
user-controlled setup; see integrations.md.
