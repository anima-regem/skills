# Token measurements

H1 was compared with the previous skill at commit `9a9afcdd17e8d09c5f321b2b3ca5c0b32b33b3bd`. The [fixture](benchmark.json) contains its exact skill text, the original eight handoffs, eight additional handoffs authored independently using the previous skill, compact H1 versions, and expected decoder output.

All sixteen compact versions were authored to retain the original facts, including restrictions, failed or skipped checks, uncertainty, attribution, and exact error strings. An independent review checked those facts. The decoder expands the codes and the `ro` macro. Shortened prose remains a summary of the original wording.

## Message tokens

Each message is tokenized independently with `tiktoken` 0.12.0. All H1 characters, spaces, and newlines count. Every fixture uses H1, including tiny updates with zero savings.

| Encoding and set | Previous skill | Expanded H1 | H1 | Reduction versus previous |
| --- | --- | --- | --- | --- |
| o200k_base, original 8 | 130 | 128 | 114 | 12.3% |
| o200k_base, additional 8 | 192 | 169 | 154 | 19.8% |
| o200k_base, all 16 | 322 | 297 | 268 | 16.8% |
| cl100k_base, original 8 | 131 | 128 | 114 | 13.0% |
| cl100k_base, additional 8 | 193 | 169 | 154 | 20.2% |
| cl100k_base, all 16 | 324 | 297 | 268 | 17.3% |

The expanded column isolates the effect of coding from prose edits. With `o200k_base`, shorter wording takes the total from 322 to 297 tokens. Replacing expanded field names and the read-only scope with H1 takes it from 297 to 268, a further 9.8% reduction. The combined improvement over the previous handoffs is 16.8%.

## Instruction costs

The shared `SKILL.md` contains the entire H1 vocabulary. Recipients that already have it can read the messages directly. Uninitialized recipients use ordinary prose until the meanings are shared. The reviewer decoder and measurement references are loaded on demand.

| Encoding | Previous instructions | H1 instructions | Previous instructions plus 16 messages | H1 instructions plus 16 messages |
| --- | --- | --- | --- | --- |
| o200k_base | 286 | 289 | 608 | 557 |
| cl100k_base | 284 | 286 | 608 | 554 |

These totals assume one full instruction load per variant. Each additional participant loading instructions adds another setup cost. At the fixture's average saving, the extra 3 tokens for H1 over the previous skill are offset within one handoff with `o200k_base`. Adding the entire H1 skill to a context that already holds the previous skill takes about 86 comparable handoffs to offset its 289 additional instruction tokens.

These are token counts for authored examples. Tool envelopes, conversation replay, caching, retries, additional negotiation, and decoder tool calls are outside the totals. Actual costs depend on the runtime and model. A short message may gain nothing from H1.

## Reproduce

Run from the repository root. The benchmark verifies all sixteen expected decoder outputs before reporting counts. The decoder itself uses the Python standard library.

```bash
uv run --isolated --with tiktoken==0.12.0 python compact-agent-handoffs/scripts/benchmark.py --encoding o200k_base
uv run --isolated --with tiktoken==0.12.0 python compact-agent-handoffs/scripts/benchmark.py --encoding cl100k_base
```
