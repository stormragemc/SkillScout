# Integrations

## Agent-Reach

Official source: https://github.com/Panniantong/Agent-Reach (MIT).
Reviewed Instagram contract: `agent-reach instagram posts USERNAME --limit N
--timeout 45`. Unified actions return a JSON envelope with top-level items.
This is experimental and browser-backed. SkillScout calls it only after explicit
Instagram enablement. The user configures sessions directly in Agent-Reach.

Never copy cookies, automate passwords or bypass blocks. Its similarly named
PyPI package is unrelated; use official GitHub setup. Report missing software,
login requirements, rate limits and schema failures. Adapter fixtures are tested;
the installing user still needs a live creator/account check.

## Earshot and video

Official source: https://github.com/Leonxlnx/earshot (MIT).
Optional `earshot measure FILE --json` supplies audio measurements. Semantic audio
commands can require models and extra dependencies. SkillScout does not initiate
model downloads or cloud audio uploads. Transcripts are supplied by the user/host;
installed ffmpeg can sample frames. Actual visual inspection is the host's task.

## SkillSpector

Official source: https://github.com/NVIDIA/SkillSpector (Apache-2.0).
Adapter target: 2.12.0 at commit 9dbf4fc75386169275e5f18c47686cb0d7274afa.
This integration requires Python 3.12+. Install separately into a dedicated
environment and expose its executable on PATH. Presence is not a clean scan.
Static analyzers can query vulnerability services depending on dependencies.
SkillScout does not pass model/API secrets to scanner subprocesses.

## Optional OpenAI review

The active host can review needs without another API call. Unattended semantic
review requires an explicit model and remote-data choice:
`skillscout model configure --name MODEL-ID --allow-remote-review`.

OPENAI_API_KEY comes from the runner's secret environment, never chat or config.
Bounded candidate instructions and setup summaries are sent to the official
Responses API with no tools. Model output cannot approve or install. No model is
selected by default. A ChatGPT subscription is not an API credential.
