# Scheduling and runner setup

Schedules store local time, IANA timezone, weekdays and source. Daily and selected
weekday schedules are supported. `schedule list` previews five upcoming runs.

Run `skillscout schedule serve` in a persistent process, or configure an OS
scheduler to call `skillscout schedule run-due` every few minutes. Saving a schedule
creates no service, startup task or ChatGPT automation. Keep the machine available.

Use a controlled local/self-hosted runner for Instagram. Configure its account
in Agent-Reach directly. Do not upload cookies, profiles or private inventories
into public CI artifacts. The template in examples/github-discovery.yml is
manually triggered by default and intended only for public GitHub discovery.

## Failure behavior

- Jobs up to an hour late can run once; older slots are skipped.
- Spring-forward nonexistent local times are skipped; repeated autumn slots run once.
- Slots are claimed before network work. Failures remain visible and can be retried manually.
- Concurrent scheduler processes are rejected. Inspect a crashed process before
  removing an abandoned lock.
- Rate limits stop the attempt; no rapid retry or account rotation.
- Model usage is bounded, but currency cost depends on your chosen model.
- Background jobs never approve or install.

Reports are Markdown/JSON in private local state, visible through the inbox.
External email, Slack and push delivery are not shipped. Configure extra channels
only as a separately authorized integration. GitHub Actions schedules can be delayed:
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows.
