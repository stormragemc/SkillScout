# Architecture

One Python runtime enforces policy. One shared Agent Skill describes the workflow.
Host manifests package that skill. The host supplies reasoning and user interaction.

| Module | Responsibility |
|---|---|
| config, core | Explicit preferences, bounded records, identities and locks |
| github | API search, historical signals and pinned safe snapshots |
| instagram, media | Opt-in creator metadata and local media evidence |
| inventory | Registered metadata/rules and BM25 overlap shortlists |
| security | Static SkillSpector execution and strict report gating |
| proposals | Need review, exact approval, staging, backup and rollback |
| reviewer | Optional bounded OpenAI review with no tools |
| schedule, reports | Due jobs, update notices and private reports |

## Ranking

GitHub candidate lanes cover agent-skills topics, README keywords and recently
created claude-code topic repositories. Lanes are interleaved and deduplicated by ID.

Relevance uses expanded term overlap over metadata. Popularity uses logarithmic
star counts. Historical momentum compares the last three completed days with the
preceding seven. The daily baseline has a five-star floor. Momentum combines
log-scaled velocity (70%) and stabilized acceleration (30%).

With history, ranking weights are relevance 45%, popularity 15%, momentum 40%.
Without it, relevance is 65% and popularity 35%. Unknown history is not zero.
The initial emerging threshold is <5,000 stars, >=10 recent stars/day and >=2x
baseline. These are transparent heuristics, not calibrated quality scores.

Historical daily counts describe star creations. Differences between current-count
snapshots measure net growth. Provider day boundaries may differ from UTC.
Creator counts cover observed handles within seven days of first observation,
not all Instagram or proof of independence.

BM25 shortlists possible overlap with existing skills/rules; it does not prove
semantic equivalence. Host/model review supplies the marginal-benefit assessment.
No inventory access means unknown coverage. Token estimates use characters/4,
not a model tokenizer. Full references load only when the host needs them.

## Approval boundary

Sources are pinned snapshots in quarantine. Final bundles retain upstream notices
and receive a second scan. Proposals bind hashes, reports, need assessment, inventory
fingerprint, target and previous destination hash. Changed data invalidates approval.

Updates require new proposals. Destination edits block overwrite. Backups support
rollback, which refuses edited installs. Local state is not a hardened consent
service, and folder copying is not persistent ChatGPT account installation.
