# Automatic skill use on a real coding task

The matched coding trial saved **9.3% of reported coordinator-plus-worker model tokens**. It missed the 70% target. Automatic activation worked, and both generated patches passed the same twelve independent acceptance checks.

## Matched result

| Measurement | Normal delegation | Automatic lean delegation |
| --- | --- | --- |
| Coordinator tokens | 770,384 | 722,255 |
| Coding-worker tokens | 460,231 | 393,451 |
| Total input plus output | 1,230,615 | 1,115,706 |
| Model requests | 30 | 27 |
| Coding workers | 1 | 1 |
| Automatic skill entry reads | 0 | 1 |
| Worker context | Default `all` | Explicit `none` |
| Independent acceptance checks passed | 12/12 | 12/12 |

The total reduction was 114,909 tokens, or 9.3375%. The coordinator reduction was 6.2%, and the worker reduction was 14.5%. Both fresh coordinators started outside this chat's history. Holding worker count at one also removes the large batching advantage from the earlier six-question experiment.

| Token detail | Normal | Automatic lean |
| --- | --- | --- |
| Input, including cached input | 1,223,462 | 1,107,965 |
| Cached input subset | 1,175,040 | 1,040,512 |
| Output, including reasoning | 7,153 | 7,741 |
| Uncached input plus output | 55,575 | 75,194 |

Uncached input plus output increased by 35.3%. That sum is an additional token metric, with no price weighting. The experiment establishes no currency-billing reduction. Cached input is counted once within input, and reasoning is counted once within output.

## Coding task and controls

The task was to reject duplicate JSON object keys in game JSONL and G2 codebooks, including escaped-equivalent names and nested duplicates, before publishing reviewer or spectator output. The coordinator delegated actual code edits and regression tests to one worker, then independently tested and reviewed the diff.

Both measured checkouts began at `231092c41ca5987ee23f41b46c6d5118a4f245a9`. They received the identical [coding brief](task.md), interpreter, prewarmed tokenizer cache, allowed-file scope, and test commands. Every measured coordinator and worker used `gpt-6.1-sol` with `high` reasoning effort and the same workspace-write sandbox. The task allowed edits only to `game.py` and `test_game.py`.

The normal checkout had a project-local, user-authorized control exception to the global lean rule. It used ordinary delegation and left the worker context option at its runtime default. The lean checkout used ordinary global instructions and installed skills. Its coding brief contained no manual skill invocation. The native audit confirms an entry-point read before delegation and an explicit isolated worker fork. The [protocol](protocol.json) includes the scoped instructions and command configuration. Global user configuration was preserved throughout.

This was one matched pair. The lean arm ran first in the measured pair, so cache warming and ordinary model variation limit generalization. It tests a small parser repair with one worker, rather than open-ended product development or a many-worker pipeline.

## Quality and retained coding outputs

The independent [acceptance harness](acceptance.py) was frozen before inspecting candidate solutions. Its SHA-256 is `6bda0b85e2e6bdcc9ec0e2b20dfedd78814a92b9320863b73c6063d7eee38c9c`. Against the original code, ten of twelve methods failed and two passed. Both measured patches passed all twelve, covering duplicate and escaped keys, nested objects, late failures, file preservation, G1/G2 replay, Unicode, and valid repeated values.

The normal arm passed 27 game tests and 11 existing benchmark tests. The lean arm passed 29 game tests and the same 11 benchmark tests. Both coordinators independently ran those suites and inspected the diff. The output patches remain [normal](normal-2.patch) and [lean](lean-1.patch) experiment artifacts for review.

Independent review found one shared diagnostic caveat. An input containing a duplicate object key and later invalid syntax can report the duplicate first, where the original parser reported `invalid JSON`. Both patches reject it safely. The frozen checks did not cover diagnostic precedence for that mixed-error case. This experiment retains the patches and does not promote either coding-arm patch into the main checkout.

## Setup pilot

An initial normal-delegation pilot exposed a tokenizer-cache location problem after the worker moved temporary files into the checkout. It completed with passing code and acceptance checks, but its setup repair makes it a different condition. Before observing any lean coding result, the protocol was amended to use an explicit shared cache for one fresh matched pair. The unused extra checkout produced no measured run.

The pilot is retained as [usage](normal-1.usage.json), [patch](normal-1.patch), and [acceptance evidence](normal-1.acceptance.log). It used 1,377,763 tokens and 32 model requests, excluded from the primary comparison. The three completed coding arms together used 3,724,084 reported model tokens and 89 requests. Observer preparation and this chat's experiment-driving work are outside those arm totals.

## Evidence and reproduction

[Normal usage](normal-2.usage.json) and [lean usage](lean-1.usage.json) contain whitelisted counters for the coordinator and its descendants, session IDs, model settings, and the tool-call audit. The collector checks the final native `token_count` total against the sum of unique native `token_usage_record` responses. It excludes replayed parent tool calls by ancestor and native turn IDs, preventing inherited-history double counting.

Raw native transcripts remain local. Published records omit account quotas, credits, private instructions, and reasoning text. Host paths in published task and log files use `$RUN_DIR` and `$HOME` placeholders. The protocol retains original task and installed-skill hashes.

Recompute the saved result without making model calls.

```bash
python3 lean-agent-handoffs/references/coding-ab-2026-11-07/analyze.py
```

To audit the original local sessions again, supply the original run directory and the relevant session-date directory.

```bash
python3 lean-agent-handoffs/references/coding-ab-2026-11-07/collect_usage.py normal-2 --run-dir "$RUN_DIR" --session-dir "$HOME/.codex/sessions/2026/11/07"
```

For a new live trial, clone the recorded base commit into fresh checkouts, use the task and scoped instructions from the protocol, prewarm the shared cache, and collect both coordinator and descendant usage. Acceptance can be run with the pinned `tiktoken==0.12.0` interpreter against each checkout. Live runs can produce different patches and usage.

To verify a saved coding patch locally without model calls, run from the repository root.

```bash
verification_run=$(mktemp -d)
git clone --quiet --no-hardlinks . "$verification_run/candidate"
git -C "$verification_run/candidate" checkout --quiet 231092c41ca5987ee23f41b46c6d5118a4f245a9
git -C "$verification_run/candidate" apply "$PWD/lean-agent-handoffs/references/coding-ab-2026-11-07/lean-1.patch"
uv run --isolated --with tiktoken==0.12.0 python -B lean-agent-handoffs/references/coding-ab-2026-11-07/acceptance.py "$verification_run/candidate"
```
