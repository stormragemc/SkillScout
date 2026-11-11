# Security and evidence

Require complete eligible SkillSpector reports for source and final bundle.
High/critical findings block installation. Medium/caution findings require
resolution and rescan. Missing tools, unknown formats, suppression, failures or
incomplete coverage cannot pass. Do not inherit candidate-controlled risk baselines.

Scans use `--no-llm --fail-on-incomplete`. Candidate code and setup hooks never
execute during inspection. Preserve dependency and coverage fields: known-CVE
lookups do not mean all dependency source bytes were inspected. The scanner
subprocess is not a hardened VM or container.

Approval binds content hashes, reports, need review, inventory fingerprint,
destination and revision. Changed state invalidates approval. Upstream notices
are copied into the final bundle. Updates preserve backups and rollback refuses
to destroy user edits.

No scanner certifies universal safety. Local state is trusted and mutable by the
account owner; CLI approval is not an identity service. Do not claim protection
against an already compromised host. Runtime dependency installation is a separate
authorized task, not an implied consequence of installing skill instructions.
