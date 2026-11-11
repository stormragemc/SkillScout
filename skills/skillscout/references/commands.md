# CLI reference

Use `skillscout --help` and subcommand `--help` for current arguments. Operational
results are JSON. Global `--home PATH` or SKILLSCOUT_HOME selects private state.
Pass source text as separate argv values; do not interpolate it into shell code.

| Task | Command |
|---|---|
| Defaults | `skillscout init` |
| Preferences | `skillscout preferences show` |
| Interests | `skillscout preferences set --interests coding design accessibility` |
| Sources | `skillscout creators list` |
| Change sources | `skillscout creators add HANDLE` / `skillscout creators remove HANDLE` |
| Allow session use | `skillscout instagram enable` |
| One-time exploration | `skillscout creators explore HANDLE` |
| Resolve posting account | `skillscout reel URL` |
| Explore that account | `skillscout reel URL --creator HANDLE --explore` |
| Monitor that account | `skillscout reel URL --creator HANDLE --watch` |
| Register skills | `skillscout inventory add-root PATH` |
| Register rules | `skillscout inventory add-rules PATH` |
| Discover | `skillscout discover --source github --limit 10 --rank trending` |
| Inspect | `skillscout inspect OWNER/REPO --skill skills/SKILL-NAME` |
| Proposal | `skillscout show ID` |
| Need review | `skillscout review ID --decision add --reason TEXT --evidence TEXT` |
| Configured model review | `skillscout review ID --model` |
| Exact approval | `skillscout approve ID --fingerprint FINGERPRINT` |
| Install approved content | `skillscout install ID` |
| Rollback | `skillscout rollback ID` |
| Inbox | `skillscout inbox` |
| Media evidence | `skillscout media VIDEO --source REEL-URL --transcript FILE --frames --audio` |
| Draft notes | `skillscout draft EVIDENCE-ID --name NAME --guidance-file FILE` |

A CLI call is not cryptographic proof of user consent. The invoking agent must
obtain approval through its host's interaction. Background jobs never invoke it.
