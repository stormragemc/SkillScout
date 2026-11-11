# SkillScout

**Find the skills your agent could use. Keep the ones it actually needs.**

SkillScout discovers AI coding and design skills on GitHub and in educational
reels from selected creators. It compares candidates with your existing setup,
inspects the exact package, and prepares a proposal. You decide what to install.

Built by [stormragemc](https://github.com/stormragemc). **OpenAI ChatGPT Work and
Codex first.** Python 3.11+ · MIT · v0.1.0

[Get started](#get-started) · [Defaults](#your-starting-defaults) ·
[First workflow](#your-first-workflow) · [Instagram](#discover-through-instagram) ·
[Scheduling](#check-on-a-schedule) · [Security](#what-the-security-check-means)

## Why this exists

You see a reel about an AI tool. You find its repository, read the setup, and try
to work out whether your agent already does the same thing. Repeat that for the
next tool, and the next. Your setup grows faster than your understanding of it.

SkillScout keeps the investigation in one place. A useful result might be:

> This project adds an audio measurement capability your registered setup does
> not appear to include. Its static inspection completed. These dependencies need
> separate setup. Review this exact version before installing.

Or simply:

> Your existing design instructions already cover this advice. Nothing to add.

Those examples illustrate the intended report, not a verdict on a scanned project.

## What happens to a candidate?

| Step | What SkillScout does |
|---|---|
| **Discover** | Search GitHub or check recent posts from configured creators. Accept direct links too. |
| **Recognize** | Extract explicit repository links; let the host agent investigate ambiguous names and demonstrations. |
| **Compare** | Shortlist overlaps with registered skills and rules. Explain the concrete capability a candidate would add. |
| **Inspect** | Pin the source commit, download into quarantine, preserve notices, and scan source plus final bundle. |
| **Review** | Record added value, conflicts, context estimates, findings and evidence. |
| **Approve** | Ask about a specific version, destination and proposal fingerprint. |
| **Install** | Copy the approved skill folder, preserve an update backup, and support rollback. |

Candidate setup scripts are never run by the inspector or installer.

## Get started

Choose the path that matches where your agent runs. A repository link by itself
does not install tools or start a background service.

### ChatGPT Work

Use a Work environment with Python and file execution. Give your agent this
repository URL and ask:

> Read SkillScout's README. Prepare the portable skill bundle for this environment,
> explain the defaults, and use the supported skill installation flow. Leave
> Instagram access, schedules and paid model calls disabled until I configure them.

The agent can obtain a source checkout and run:

```sh
python scripts/build_bundle.py
```

This creates **dist/skillscout.zip**: the skill, references and a self-contained
Python runtime. Building does not install it. Use your host's supported skill
installation workflow. The repository's [CI runs](https://github.com/stormragemc/SkillScout/actions/workflows/ci.yml)
also produce a portable bundle artifact once package checks pass.

Then ask:

> Use SkillScout to show my defaults, then find promising coding and design skills.

Plain chat without code/tool execution can discuss reports but cannot run the CLI.
This is a skill package, not a hosted MCP service or a public-directory listing.
See [installation by host](docs/INSTALLATION.md).

### Local Codex or a terminal

Review the source. With [uv](https://docs.astral.sh/uv/) installed:

```sh
uv tool install git+https://github.com/stormragemc/SkillScout.git
skillscout init
skillscout integrations
skillscout discover --source github --limit 5
```

Or use a virtual environment from a source checkout:

```sh
python -m venv .venv
# macOS / Linux
.venv/bin/python -m pip install .
.venv/bin/skillscout init
```

```powershell
# Windows PowerShell; no activation-policy changes required
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\skillscout.exe init
```

Use this repository URL, not an assumed same-named PyPI package. SkillScout needs
Python 3.11+; the separate SkillSpector integration needs Python 3.12+.

Install the shared skill at **skills/skillscout** with your supported Codex skill
installer, alongside the CLI. Standard plugin packaging is included:
`plugin.json`, `.codex-plugin/plugin.json`, and
`.agents/plugins/marketplace.json`. A copied source-only skill needs the installed
CLI; the portable ZIP includes its runtime.

Claude Code and Gemini manifests use the same shared skill. They are secondary
adapters, with live installation checks still pending.

## Your starting defaults

Setup explicitly displays these settings:

| Setting | Default |
|---|---|
| Interests | General: **coding and design** |
| Primary target | Codex / OpenAI |
| Instagram watchlist | The five creators below |
| Instagram session access | Disabled |
| Schedules | None |
| Paid model review | Disabled; no model selected |
| Installation | Explicit approval of each inspected proposal |

Default discovery sources:

- [@nocode.joshua](https://www.instagram.com/nocode.joshua/)
- [@nick_saraev](https://www.instagram.com/nick_saraev/)
- [@canwebuildthis](https://www.instagram.com/canwebuildthis/)
- [@byjoeym](https://www.instagram.com/byjoeym/)
- [@itsmariahbrunner](https://www.instagram.com/itsmariahbrunner/)

These are maintainer-selected starting sources, not security endorsements.
Keep, remove or replace them. Reinitializing does not restore creators you removed.

Tell your agent “Focus on accessibility from now on,” “Show my sources,” or
“Remove this creator.” It translates those choices into saved settings.

```sh
skillscout preferences show
skillscout preferences set --interests coding design accessibility
skillscout creators list
skillscout creators remove nick_saraev
```

For a one-off interest change, ask the agent to use temporary preferences and
restore them afterward. Persistent changes should be explicit.

## Your first workflow

### 1. Show what your agent already has

Register the directories and particular rules files you want considered:

```sh
skillscout inventory add-root /path/to/your/skills
skillscout inventory add-rules /path/to/your/DESIGN.md
skillscout inventory show
```

Only registered scope is read. SkillScout does not crawl your home directory,
read browser credentials or access chat memories your host does not expose.
An empty inventory means unknown coverage, not proof of a missing capability.

### 2. Find a candidate

```sh
skillscout discover --source github --limit 10
skillscout discover --source github --limit 10 --rank trending
skillscout inbox
```

You get candidates, setup-overlap shortlists, JSON records and a local Markdown
report. Popularity is a discovery signal, not an installation recommendation.

### 3. Inspect a particular package

```sh
skillscout inspect OWNER/REPOSITORY
```

If several skills are found, choose the relative folder shown in the result:

```sh
skillscout inspect OWNER/REPOSITORY --skill skills/SKILL-NAME
```

The proposal records its ID, pinned revision, scanner results, context estimates
and existing-setup comparison. A tool-only repository receives manual integration
guidance; SkillScout does not run its installer.

### 4. Ask whether it is worth adding

Ask your agent: “Compare this proposal with my setup. Does it add a useful
capability? Explain the evidence and conflicts before asking me to install.”

The agent records a decision:

```sh
skillscout review PROPOSAL-ID --decision add --reason "EXPLAIN THE GAP" --evidence "CITE INSPECTED SOURCES AND ACTUAL TEST COVERAGE"
skillscout show PROPOSAL-ID
```

Decisions are **add**, **update**, **redundant**, **conflict**, or **uncertain**.
Recording evidence does not prove that a runtime test occurred.

### 5. Approve, then install

Review the proposed changes. After you explicitly approve that exact proposal:

```sh
skillscout approve PROPOSAL-ID --fingerprint EXACT-FINGERPRINT
skillscout install PROPOSAL-ID
```

Changed content, inventory or destination invalidates approval. Security checks
must still be eligible. Every update requires a fresh inspected proposal.

```sh
skillscout rollback PROPOSAL-ID
```

Rollback restores an update backup or removes an unchanged new install. It refuses
to destroy edits you made after installation.

## Discover through Instagram

Install and configure [Agent-Reach](https://github.com/Panniantong/Agent-Reach)
separately using its official GitHub instructions. The similarly named PyPI package
is unrelated. Its Instagram integration is experimental and can use your configured
browser account. SkillScout does not log in or export cookies.

After reviewing that session access:

```sh
skillscout instagram enable
skillscout discover --source instagram
```

When you submit a reel:

```sh
skillscout reel https://www.instagram.com/reel/SHORTCODE/
```

SkillScout attempts to identify the posting account through public structured
metadata. Your agent offers **Explore this creator once** or **Add to my watchlist**.
They are separate choices. When metadata is inaccessible, an authorized browser
can resolve the account and supply it explicitly:

```sh
skillscout reel REEL-URL --creator HANDLE --explore
skillscout reel REEL-URL --creator HANDLE --watch
```

The automated feed adapter currently reads **recent-post metadata and captions**.
It extracts explicit GitHub links and tracks creator coverage. The host agent
handles semantic name matching, additional authorized searches and visual review.
A caption is never presented as a watched video.

For accessible media you or your host provide:

```sh
skillscout media ./reel.mp4 --source REEL-URL --creator HANDLE --transcript ./transcript.txt --frames --audio
```

An installed ffmpeg samples frames; the host must inspect them. An installed
[Earshot](https://github.com/Leonxlnx/earshot) measures audio. Transcription is
supplied separately. No hidden speech-model downloads or cloud audio uploads.
Video-only guidance can be saved as sourced draft notes, not installed as a
supposedly validated skill.

## How “up-and-coming” is measured

Discovery combines topic relevance, logarithmically scaled total stars and recent
momentum where history is available. Established and new search lanes are
interleaved so large projects cannot occupy every slot.

Momentum considers recent stars per day and acceleration against a baseline,
with a floor to prevent tiny counts producing dramatic ratios. Initial emerging
thresholds are **under 5,000 total stars, at least 10 recent stars/day, and at least
2x the stabilized baseline**. These are starting heuristics, not a calibrated
quality model.

Missing history stays unknown. Creator coverage counts observed distinct accounts
within a recent window, not all Instagram or proven independent endorsements.
Stars and views never override security or the need assessment.
[Read the ranking details](docs/ARCHITECTURE.md).

## Check on a schedule

Tell your agent when and where to check, or configure it directly:

```sh
skillscout schedule set github-morning --source github --at 09:15 --timezone Asia/Singapore --days daily
skillscout schedule set creator-weekend --source instagram --at 18:30 --timezone Asia/Singapore --days sat
skillscout schedule list
skillscout schedule serve
```

The last command runs the scheduler in the foreground. Keep the runner available,
or have an OS scheduler call `skillscout schedule run-due`. Saving a schedule does
not start a service or make a closed chat execute.

Runs prepare a private inbox. When you return, ask your agent to review it.
**Background jobs cannot approve or install.** External notification delivery is
not configured in v0.1.

```sh
skillscout schedule pause creator-weekend
skillscout schedule resume creator-weekend
skillscout preferences set --candidates 10 --posts-per-creator 6 --model-calls 2
```

[Runner setup and failure behavior](docs/SCHEDULING.md).

### Optional unattended model review

Your active agent can assess needs interactively. To review while that
conversation is closed, explicitly configure a model:

```sh
skillscout model configure --name YOUR-MODEL-ID --allow-remote-review
```

Set **OPENAI_API_KEY** in your runner's supported secret environment, never chat
or preferences. Bounded candidate instructions and setup summaries go to the
official OpenAI Responses API. A ChatGPT subscription is not an API key.

The model receives no tools, and cannot approve, install or bypass scanner
results. Input-size, output-token and per-run call limits are enforced; these
usage limits are not a guaranteed dollar cap.

## What the security check means

SkillScout integrates [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector).
Install it separately in a dedicated Python 3.12+ environment.
[Setup and pinned adapter target](docs/INSTALLATION.md#optional-integrations).

| Result | Installation policy |
|---|---|
| High or critical finding | Blocked |
| Medium finding or caution verdict | Resolve and rescan |
| Missing scanner, unknown schema, suppression, failed or incomplete scan | Unverified; blocked |
| Complete configured checks with no blocking findings | Eligible for explicit approval |

Both original source and final package are hashed and screened. Source notices
are preserved. Candidate-controlled risk suppressions are not passed to the scanner.

**Eligible means “no blocking issues detected by these checks.”** Static analysis
cannot guarantee safety or inspect code downloaded in the future. The scanner
process is not a hardened VM. Local state does not defend against an account
already controlled by another process. [Read the trust model](SECURITY.md).

## Current limits

- Instagram requires a live check in your configured account. Access errors and
  changed schemas are reported, not bypassed.
- Automatic reel downloading and speech transcription are not implemented.
  Feed metadata is automated; full video evidence uses supplied accessible media.
- Need review is an evidence-based judgment, not a universal proof of usefulness.
- Arbitrary runtime installers and execution-based benchmarking of every repo
  are outside v0.1.
- Claude Code and Gemini live installation remain unverified.
- Copying a folder into a sandbox is not persistent ChatGPT account installation;
  use that host's supported skill workflow.

## Contributing

```sh
python -m unittest discover -s tests -v
python scripts/build_bundle.py
python scripts/check_package.py
```

Tests use temporary state. The portable package is built and checked in CI.
Fixtures, live checks and untested paths are distinguished in
[VALIDATION.md](docs/VALIDATION.md).

[Contributing](CONTRIBUTING.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Security](SECURITY.md) · [Credits](THIRD_PARTY_NOTICES.md)

SkillScout is MIT licensed. Integrated projects retain their own licenses.
No affiliation with OpenAI, Anthropic, Google, NVIDIA or the listed creators
is implied.
