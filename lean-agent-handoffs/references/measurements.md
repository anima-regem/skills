# Handoff A/B measurements

Observed savings depend on the workflow. A later [real coding trial](coding-ab-2026-11-07/REPORT.md) confirmed automatic skill use but saved only **9.3%** of coordinator-plus-worker tokens, missing the 70% target. Both patches passed twelve independent acceptance checks. The earlier read-only runs below reached the target through batching and isolated task context. Exact one-off message encoding is a separate problem, and the codec experiment below found no gain over H1.

## Reported child-model usage

Six distinct, read-only questions about Python functions were answered by independent agents with complete files or dependency-complete excerpts. A second pair of agents answered all six questions in one batch. Model settings were inherited from the same parent. Each child made one tool call to read its packet and then returned JSON, taking two model requests. All answers matched the frozen Boolean facts.

The questions cover narrow behaviors in this repository's two handoff scripts. Broader code-review quality requires separate evaluation.

| Strategy | Child agents | Model requests | Reported input plus output tokens | Reduction versus separate full-source handoffs |
| --- | --- | --- | --- | --- |
| Separate full-source handoffs | 6 | 12 | 389,049 | baseline |
| Separate selected-source handoffs | 6 | 12 | 375,548 | 3.5% |
| Batched full-source handoff | 1 | 2 | 66,184 | 83.0% |
| Batched selected-source handoff | 1 | 2 | 64,050 | 83.5% |

This comparison includes fixed child instructions and tool context, which dominate these short tasks. Selecting source alone saves little at that level. The stronger already-batched control is also shown. Selected source saves 3.2% against that control. Batching trades parallel work for fewer model requests, and fits related independent questions sharing source context.

An additional one-off usage check compared the default inherited chat context with an isolated selected-source handoff for the same publication question.

| One-off context | Model requests | Reported input plus output | Cached input subset | Uncached input plus output |
| --- | --- | --- | --- | --- |
| Inherited long chat and full source | 2 | 470,137 | 466,432 | 3,705 |
| Isolated context and selected source | 2 | 62,599 | 61,824 | 775 |

The observed reduction was 86.7% in total reported tokens and 79.1% in uncached input plus output. This tests the combined context policy in this existing long chat. A short parent chat can yield a much smaller benefit. The inherited branch could see earlier discussion of the answer, so this additional pair measures usage and answer consistency rather than blinded answer quality. The earlier twelve isolated runs separately validate the excerpt answers.

Native counters are the final `token_count.info.total_token_usage` records from these child sessions. Published records contain whitelisted counters, the dispatch, raw final answers, model/tool-call counts, and provenance. The provenance records session IDs, usage-event timestamps, and the observed `gpt-6.1-sol` model with `ultra` reasoning effort for all arms. The local native events were checked directly during collection. The replay script verifies arithmetic and matched settings, while original native sessions remain local evidence.

Total tokens equal input plus output. Cached input is already part of input, and reasoning output is already part of output. Parent planning, benchmark research, and preparation costs are outside these child-run totals. Currency billing was not measured, and cache prices can change the monetary ratio.

## Handoff-content proxy

The six paired prompts use identical ordinary-English questions, output schemas, and restrictions. The lean arm selects exact functions, imports, and manually identified local dependencies. The fixture projector selects named definitions and preserves their decorators. It relies on the supplied dependency list. Both arms preserve the required facts. This measures task-context selection, rather than an effect of invented words.

| Encoding | Full-source dispatch, context, and replies | Lean dispatch, context, replies, and setup | Reduction |
| --- | --- | --- | --- |
| o200k_base | 15,253 | 3,254 | 78.7% |
| cl100k_base | 14,962 | 3,195 | 78.6% |

The proxy charges a full read of the current automatically invoked skill for every lean handoff, 199 tokens under `o200k_base` or 197 under `cl100k_base`. Individual paired reductions range from 71.7% to 82.2%. Both arms answered all six questions correctly, with no additional context retrieval. Tool/system envelopes and private reasoning belong to the separate native-usage measurement above, rather than this tokenizer proxy. Native observations were collected before the automatic-activation wording was added.

## Review and reproduce

The [fixture](ab-fixture.json) freezes source from `anima-regem/skills` commit `8ba73cbac6c924535a8ae427515eccb1beaf3555`, the six questions, selected definitions, and acceptance facts. [Individual runs](ab-runs.json), [batch runs](ab-batches.json), and [context runs](ab-context.json) preserve raw answers and counters. Reviewers can reconstruct each prompt and compare every answer with its stated task.

These are controlled examples with one observed run per arm and question, rather than a statistical guarantee. Broader tasks can require more context, additional exchanges, or separate agents. The skill retains needed context and records a missed target in those cases.

Run from the repository root to regenerate packets and score the saved observations.

```bash
task_run=$(mktemp -d)
uv run --isolated --with tiktoken==0.12.0 python -B lean-agent-handoffs/scripts/benchmark.py prepare "$task_run/packets"
uv run --isolated --with tiktoken==0.12.0 python -B lean-agent-handoffs/scripts/benchmark.py report lean-agent-handoffs/references/ab-runs.json --encoding o200k_base
uv run --isolated --with tiktoken==0.12.0 python -B lean-agent-handoffs/scripts/benchmark.py report lean-agent-handoffs/references/ab-runs.json --encoding cl100k_base
uv run --isolated --with tiktoken==0.12.0 python -B -m unittest discover -s lean-agent-handoffs/scripts -p test_benchmark.py -v
```

To collect new observations, dispatch each prepared packet to fresh agents with matching model settings and explicit `fork_turns="none"`. Record exact final JSON and all extra retrievals, then whitelist native usage counters. For the batch control, dispatch the corresponding batch packet once. Live token counts depend on the runtime and current context, and can differ from the saved run.

## Other methods tested

The game benchmark tests tokenizer IDs, repeated-message codebooks, and 35 one-off codec/rendering combinations. All 28 unique one-off messages grew under the tested exact encodings, including two longer handoffs. The [codec results](https://github.com/anima-regem/skills/blob/main/compact-agent-handoffs/references/oneoff-measurements.md) explain that limit. Readable tasks with less inherited context and fewer exchanges produced the observed large savings here.
