---
name: lean-agent-handoffs
description: Reduce main-agent and subagent handoff tokens through complete task context, batching, and fewer exchanges.
---

# Lean Agent Handoffs

Batch related independent questions before spawning. For isolated work, use `fork_turns="none"`. Send the goal, scope, required result, and minimal exact source with its dependencies. Preserve restrictions, uncertainty, and checks. Request missing context when it affects the answer.

Send changed facts and one delivered completion. Keep handoffs and reviewer logs readable.

Target at most 30% of baseline reported child-model tokens. Count setup, briefs, context, replies, and retrievals. Distinguish payload estimates from full usage and billing. Verify quality before claiming savings. Retain necessary context when the target cannot be met.

See [A/B measurements](references/measurements.md) for the tested scope and cost limits.
