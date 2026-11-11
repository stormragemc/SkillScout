# Security

Report suspected vulnerabilities privately through GitHub's private vulnerability
reporting if available. Otherwise open an issue requesting a private channel,
without exploit details, credentials or private source material.

## Trust boundaries

Trusted components are SkillScout, the installed scanner, the host permission
system, the selected model endpoint and local user state. Candidate content is
untrusted. Popularity grants no authority.

Candidate setup hooks and lifecycle scripts are not executed. Installation copies
one selected skill folder. Runtime integration setup is a separate authorized task.

GitHub acquisitions are pinned and constrained to allowed HTTPS hosts. Extraction
rejects traversal, links, special files, collisions and resource limits.
Scanner subprocesses use bounded time/output and a reduced environment. This is
defense in depth, not a hardened VM/container sandbox.

High/critical findings block. Medium/caution findings require resolution and
rescan. Unknown schemas, suppressions, incomplete coverage and failures are
unverified. There is no force-install switch. Dependency declaration/CVE checks
are not complete audits of all transitive source bytes.

Eligible scans are not guarantees. Review actual permissions, external downloads,
licenses, declared purpose and behavior. Candidate-controlled baselines are not
passed to the scanner.

## Consent and privacy

Approval is bound to a proposal fingerprint. The host must obtain explicit user
approval; a CLI call cannot prove who made the decision. An account/process with
write access to local state can alter it. This is not protection against an
already compromised host.

State can contain private rules and captions. Keep it out of Git. Remote model
review is disabled by default. Enabling it permits bounded candidate text and
setup summaries to be sent to the official OpenAI API. Keys come from the runner
environment, not preferences. The review model has no tools.

Instagram uses Agent-Reach's configured session after explicit enablement.
SkillScout does not import/export cookies, log in or bypass access restrictions.

## Recovery

An update is staged beside its destination. A backup is verified before moving
the old folder. Ordinary filesystem errors restore the previous version.
Power loss during replacement can require manual recovery from backups. Check
records and contents before deleting them. Rollback refuses to destroy user edits.
