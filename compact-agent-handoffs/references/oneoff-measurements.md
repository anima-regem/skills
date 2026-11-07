# Exact one-off encoding measurements

The experiment tests whether reversible encodings can make unique H1 messages smaller while allowing exact reviewer recovery. It uses the original sixteen [H1 cases](benchmark.json) and twelve independently authored [fresh cases](oneoff-cases.json), including two longer handoffs. Each set contains unique messages. The benchmark checks byte-exact recovery before counting tokens.

The matrix combines seven codecs with five text renderings, giving 35 candidates per message.

- Codecs include raw bytes, zlib, raw DEFLATE, gzip, bzip2, LZMA, and Brotli.
- Renderings include Base64, ASCII85, Base85, decimal integers, and tokenizer-native words.

Native-word packing derives a deterministic power-of-two alphabet from tokenizer IDs whose bytes match a leading space and ASCII letters. It packs compressed bytes into that radix, using a sentinel to retain leading zero bytes. The alphabet carries 16 bits per word for `o200k_base` and 15 for `cl100k_base`.

## Results

The best uniform candidate was Brotli with native-word packing. Every candidate increased every message's payload count in these sets. Event counts include the actual JSON metadata, message IDs, routes, encoding/codec/rendering selectors, escaping, and trailing newline.

| Encoding and set | H1 bodies | Best encoded bodies | H1 events | Best encoded events | Per-message body wins |
| --- | --- | --- | --- | --- | --- |
| o200k_base, original 16 | 268 | 521 | 646 | 1,298 | 0 |
| o200k_base, fresh 12 | 692 | 916 | 982 | 1,499 | 0 |
| cl100k_base, original 16 | 268 | 553 | 612 | 1,312 | 0 |
| cl100k_base, fresh 12 | 696 | 974 | 960 | 1,543 | 0 |

Even selecting the cheapest framed candidate separately for each message gave 1,284 and 1,497 tokens for the original and fresh sets under `o200k_base`, both above H1. Under `cl100k_base`, those totals were 1,290 and 1,539. That selection is an optimistic oracle bound, rather than a deployed game format.

Each encoding run validates 980 exact round trips. The counts assume the standard decoder algorithms and tokenizer vocabulary are available, with no extra model prompt charged for decoder code. Adding setup would increase the encoded cost. Raw H1 values, errors, Unicode, and all source facts remain intact in the recovery checks.

The tested codecs support no claim of cheaper exact one-off H1 encoding. The repository's [lean handoff skill](https://github.com/anima-regem/skills/tree/main/lean-agent-handoffs) instead measures savings from context isolation, source selection, and batching. Its logs preserve readable tasks and results.

## Reproduce

Run from the repository root with pinned packages. First use can download packages and tokenizer vocabularies.

```bash
uv run --isolated --with tiktoken==0.12.0 --with brotli==1.1.0 python -B compact-agent-handoffs/scripts/benchmark_oneoff.py --encoding o200k_base
uv run --isolated --with tiktoken==0.12.0 --with brotli==1.1.0 python -B compact-agent-handoffs/scripts/benchmark_oneoff.py --encoding cl100k_base
```
