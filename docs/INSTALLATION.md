# Installation by host

## ChatGPT Work

Use a Work environment with Python/file execution. Obtain and review the source,
then run `python scripts/build_bundle.py`. The ZIP contains a single skillscout
folder with SKILL.md, references and scripts/runtime. Install through your host's
supported skill workflow: https://learn.chatgpt.com/docs/build-skills.

For subsequent candidate skills, set `preferences set --delivery work` before
inspection. After exact approval use `export ID --output ./approved-skill.zip`,
then Work's supported installer. Exporting does not install. Cloud versioning
and rollback belong to that host; CLI rollback applies only to local installs.

This is not an OAuth connector or hosted MCP service. Running a CLI on another
machine does not expose tools to this chat. Skill upload/GitHub import controls
can vary by host and workspace permissions. Plain chat cannot run the runtime.

## Codex

Install the CLI in a dedicated environment. Install skills/skillscout with the
supported skill installer, or use the self-contained bundle. Local skill discovery
uses .agents/skills. Keep user and repository-scoped installations separate.

The repo includes .agents/plugins/marketplace.json, root plugin.json and the
.codex-plugin compatibility overlay. They share the same skills directory.
A copied source-only skill still needs the separately installed CLI.

## Secondary hosts

.claude-plugin/plugin.json and its marketplace expose the shared skill.
gemini-extension.json and GEMINI.md provide Gemini packaging. Structural checks
do not establish live-host acceptance. Follow each host's current installation guide.

## Optional integrations

The core runtime uses the standard library. Windows package installs include tzdata.

| Integration | Official source | Setup |
|---|---|---|
| Agent-Reach | https://github.com/Panniantong/Agent-Reach | User-controlled browser/session; experimental Instagram |
| Earshot | https://github.com/Leonxlnx/earshot | User-installed audio dependencies |
| SkillSpector | https://github.com/NVIDIA/SkillSpector | Separate Python 3.12+ environment |
| ffmpeg | https://ffmpeg.org/ | User-installed frame extractor |

After reviewing upstream source, install the tested scanner version:

```sh
uv tool install 'skillspector @ git+https://github.com/NVIDIA/SkillSpector.git@9dbf4fc75386169275e5f18c47686cb0d7274afa'
```

Expose its executable on PATH. SkillScout does not run integration installers
automatically. `integrations` checks presence, not accounts or live access.
Follow official Agent-Reach setup; the similarly named PyPI package is unrelated.

State defaults to ~/.skillscout, configurable with --home or SKILLSCOUT_HOME.
Keep it outside public repositories: it can contain private inventories, reports,
captions, decisions, snapshots and backups.
