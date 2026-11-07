---
name: compact-agent-handoffs
description: Use compact H1 handoffs for multi-agent work or render game dialogue as token-ID spectator messages with decoded reviewer logs.
---

# Compact Agent Handoffs

Use H1 when both agents share this skill. Each line is one code, one space, and literal text. The codes expand as follows.

`T` Task, `U` Update, `D` Done, `B` Blocked, `Q` Ask, `S` Scope, `C` Check, `N` Next.

`S ro` expands to `Scope: Read only.` Other field contents stay literal.

```text
D src/auth.ts:74 added missing return
C auth tests 12 passed; full suite not run
```

Give new recipients the goal, context, and limits. Then send changed facts. Preserve exact identifiers, attribution, uncertainty, failed or skipped checks, and remaining work. Link accessible evidence. Batch related updates and reuse delivered completions.

Use normal agent channels and reachable IDs. `send_message` delivers updates; `followup_task` wakes idle non-root agents. Relay through a reachable parent when needed.

Prefer plain language for uninitialized recipients, shorter messages, multiline literals, ambiguity, or approvals. Keep exchanges in the normal transcript.

Reviewers can use the [decoder](references/decoder.md). See [measurements](references/token-measurements.md) for savings and setup costs.

For a token-ID spectator view with decoded reviewer logs, use [game mode](references/game.md).
