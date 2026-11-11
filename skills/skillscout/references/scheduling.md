# Scheduling

Examples:

```sh
skillscout schedule set morning --source github --at 09:15 --timezone Asia/Singapore --days daily
skillscout schedule set weekend --source instagram --at 18:30 --timezone Asia/Singapore --days sat
skillscout schedule list
```

Run `schedule serve` on an available machine/runner, or have an OS scheduler call
`schedule run-due` every few minutes. Saving schedules starts no process, keeps no
computer awake and creates no ChatGPT automation. Repeated autumn times run once;
spring-forward gaps are skipped. Jobs up to an hour late can run once; older jobs
are skipped. Failed claims remain visible and need manual retry. A crash may
leave a lock; verify no active process before removing an abandoned lock.

Runs create local Markdown/JSON reports. Optional configured OpenAI review
processes a budgeted shortlist after screening. No background job approves or
installs. External notifications are not configured by v0.1. Never upload browser
sessions or personal inventories into public CI artifacts.
