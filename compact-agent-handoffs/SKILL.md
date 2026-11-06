---
name: compact-agent-handoffs
description: Reduce message tokens in parent, peer, and child agent handoffs during multi-agent work.
---

# Compact Agent Handoffs

Use the shortest clear message. Start longer handoffs with `Task`, `Update`, `Done`, `Blocked`, or `Ask`. Add `Scope`, `Check`, or `Next` as needed. Recipients can reply in ordinary language.

```text
Done: Fixed redirect loop at src/auth.ts:74.
Check: 12 auth tests passed. Full suite not run.
```

- Give new recipients the goal, context, and limits. Then send changed facts. Keep exact identifiers, uncertainty, failed or skipped checks, and remaining work that affects the next action. Link evidence the recipient can access.
- Batch related updates when timing permits. Skip routine acknowledgments. Use the platform's delivered completion as the result when it reaches the intended recipient. Attribute any findings you relay.
- Use normal agent channels and reachable IDs or canonical paths. In Codex, `spawn_agent` takes the initial task, `send_message` delivers updates, and `followup_task` wakes idle non-root agents. Relay through a reachable parent if needed.
- Keep messages readable in the transcript. Expand ambiguous requests and use plain language for approvals and decisions needing human review.

See [token measurements](references/token-measurements.md) when evaluating savings.
