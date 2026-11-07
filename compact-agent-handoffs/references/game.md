# Spectator game mode

G1 renders recorded or synthetic H1 game dialogue as tokenizer IDs for spectators. Reviewers receive separate logs containing the exact H1 and its expanded fields. Normal agent coordination remains readable in the usual transcript. Deliver the spectator output to players and the reviewer log to reviewers.

Each spectator record carries a message ID, sender, recipient, encoding name, installed `tiktoken` version, and a numeric `tokens` array. The content uses actual tokenizer IDs. The public vocabulary makes this a reversible puzzle display, and a player with the decoder can recover it. The game mode increases token counts when its numeric output is sent back to a model.

## Create both views

Use Python 3.9 or later with `uv`. Run from the repository root. This example creates a fresh output directory for each run and uses the included two-message [dialogue](game-dialogue.jsonl).

The first run may download the Python package and tokenizer vocabulary. For offline play, run the example once with network access to warm both caches, then retain them on the game host.

```bash
game_output=$(mktemp -d)
uv run --isolated --with tiktoken==0.12.0 python -B compact-agent-handoffs/scripts/game.py encode compact-agent-handoffs/references/game-dialogue.jsonl --reviewer-log "$game_output/reviewer.jsonl" > "$game_output/spectator.jsonl"
uv run --isolated --with tiktoken==0.12.0 python -B compact-agent-handoffs/scripts/game.py decode "$game_output/spectator.jsonl" > "$game_output/replayed.jsonl"
cmp "$game_output/reviewer.jsonl" "$game_output/replayed.jsonl"
```

Use `cat "$game_output/spectator.jsonl"` for the encoded view and `cat "$game_output/reviewer.jsonl"` for the readable review. The commands also accept `-` for stdin. Use `--encoding cl100k_base` to select the other supported vocabulary. Replay uses the encoding and package version recorded in each event.

Input is UTF-8 JSONL with exactly four nonempty string fields per message.

```json
{"id":"m1","from":"scout","to":"builder","h1":"T inspect map for exits\nS ro"}
```

The corresponding spectator record has this form.

```json
{"format":"G1","tokenizer":"0.12.0","encoding":"o200k_base","id":"m1","from":"scout","to":"builder","tokens":[51,36665,4014,395,93706,198,50,974]}
```

Its reviewer record retains the exact H1 alongside the decoded meaning.

```json
{"format":"G1-review","tokenizer":"0.12.0","encoding":"o200k_base","id":"m1","from":"scout","to":"builder","h1":"T inspect map for exits\nS ro","decoded":"Task: inspect map for exits\nScope: Read only."}
```

The encoder validates the whole batch, checks unique message IDs, and derives reviewer text from the token IDs. It publishes a complete reviewer log before emitting any spectator records. Existing reviewer files are preserved. If spectator output fails after publication, the complete prepared dialogue remains in the reviewer log. Use a fresh log path when retrying a completed batch.

The decoder checks vocabulary/version metadata, integer token IDs, strict UTF-8, canonical ordinary encoding, and H1 syntax. Special-token spellings in H1 text are handled as literal text. Replay reconstructs the prepared dialogue, with ordinary H1 [field meanings](decoder.md).

## Benchmark against H1

The final serializer was measured on the same sixteen [H1 fixtures](benchmark.json). Every message is tokenized separately using `tiktoken` 0.12.0. Numeric array columns include brackets and commas. Event columns include all JSON keys, sender/recipient IDs, metadata, escaping, and the final newline.

| Representation | o200k_base tokens | cl100k_base tokens |
| --- | --- | --- |
| H1 message bodies | 268 | 268 |
| Numeric ID arrays | 713 | 709 |
| Plain H1 JSONL events | 646 | 612 |
| Full spectator JSONL events | 1,378 | 1,324 |
| Decoded reviewer JSONL events | 1,346 | 1,296 |
| Spectator plus reviewer events | 2,724 | 2,620 |

Numeric arrays cost 2.66 times the H1 bodies with `o200k_base`, and 2.65 times with `cl100k_base`. Including event envelopes, the spectator view costs 2.13 and 2.16 times the corresponding plain H1 events. This measures the cost of passing the rendered text to a model. Local encoding and display themselves make no model calls.

For the `o200k_base` run, spectator storage was 3,449 UTF-8 bytes and reviewer storage was 4,924 bytes. All sixteen H1 texts and expanded reviewer messages round-tripped exactly under both encodings. Token counts exclude model instruction loads, tool envelopes, caching, conversation replay, and any game frontend. The [H1 benchmark](token-measurements.md) separately measures handoff and instruction costs.

Reproduce the measurements and boundary checks with these commands.

```bash
uv run --isolated --with tiktoken==0.12.0 python -B compact-agent-handoffs/scripts/benchmark_game.py --encoding o200k_base
uv run --isolated --with tiktoken==0.12.0 python -B compact-agent-handoffs/scripts/benchmark_game.py --encoding cl100k_base
uv run --isolated --with tiktoken==0.12.0 python -B -m unittest discover -s compact-agent-handoffs/scripts -p test_game.py -v
```

The implementation uses the public ordinary encoding and strict decoding APIs documented in the pinned [tiktoken source](https://github.com/openai/tiktoken/blob/0.12.0/tiktoken/core.py).
