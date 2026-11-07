#!/usr/bin/env python3
"""Compare exact reversible one-off encodings with unique H1 messages."""

import argparse
import base64
import bz2
import gzip
import json
import lzma
import re
import zlib
from collections import Counter
from functools import partial
from importlib.metadata import version
from pathlib import Path

import brotli
import tiktoken

from game import ENCODINGS, json_line


def raw_deflate(data: bytes) -> bytes:
    compressor = zlib.compressobj(level=9, wbits=-15)
    return compressor.compress(data) + compressor.flush()


def number_bytes(number: int) -> bytes:
    restored = number.to_bytes((number.bit_length() + 7) // 8, "big")
    if restored[:1] != b"\x01":
        raise ValueError("missing byte-preservation sentinel")
    return restored[1:]


def word_alphabet(encoding) -> tuple:
    words = []
    for token in range(encoding.n_vocab):
        try:
            data = encoding.decode_single_token_bytes(token)
        except KeyError:
            continue
        if re.fullmatch(rb" [A-Za-z]+", data):
            words.append(data.decode("ascii"))
    bits = len(words).bit_length() - 1
    alphabet = words[:1 << bits]
    return alphabet, {word: index for index, word in enumerate(alphabet)}, bits


def pack_words(data: bytes, alphabet: list, bits: int) -> str:
    number = int.from_bytes(b"\x01" + data, "big")
    mask = (1 << bits) - 1
    words = []
    while number:
        words.append(alphabet[number & mask])
        number >>= bits
    return "".join(reversed(words))


def unpack_words(text: str, indexes: dict, bits: int) -> bytes:
    number = 0
    for word in text.split(" ")[1:]:
        number = (number << bits) | indexes[" " + word]
    return number_bytes(number)


def benchmark(cases: list, label: str, encoding, compressors: dict, renderings: dict) -> None:
    def tokens(text: str) -> int:
        return len(encoding.encode_ordinary(text))

    messages = [case["h1"] for case in cases]
    if len(set(messages)) != len(messages):
        raise ValueError(f"{label} contains repeated messages")
    baseline_bodies = [tokens(message) for message in messages]
    baseline_events = []
    candidates = {
        (codec, rendering): {"body": [], "event": []}
        for codec in compressors
        for rendering in renderings
    }
    roundtrips = 0
    for case in cases:
        source = {"id": case["id"], "from": "/root/worker", "to": "/root", "h1": case["h1"]}
        baseline_events.append(tokens(json_line(source)))
        original = case["h1"].encode("utf-8", errors="strict")
        for codec, (compress, decompress) in compressors.items():
            compressed = compress(original)
            for rendering, (render, restore) in renderings.items():
                payload = render(compressed)
                restored = decompress(restore(payload))
                if restored != original:
                    raise ValueError(f"round-trip failure for {case['id']}: {codec}/{rendering}")
                event = {
                    "id": case["id"],
                    "from": source["from"],
                    "to": source["to"],
                    "format": "oneoff-v1",
                    "encoding": encoding.name,
                    "codec": codec,
                    "rendering": rendering,
                    "payload": payload,
                }
                counts = candidates[codec, rendering]
                counts["body"].append(tokens(payload))
                counts["event"].append(tokens(json_line(event)))
                roundtrips += 1

    before_bodies, before_events = sum(baseline_bodies), sum(baseline_events)
    print(f"{label}: {len(cases)} unique messages; H1 bodies {before_bodies}; H1 events {before_events}")
    for criterion in ("body", "event"):
        best = min(candidates, key=lambda key: sum(candidates[key][criterion]))
        counts = candidates[best]
        wins = sum(after < before for after, before in zip(counts["body"], baseline_bodies))
        print(
            f"  Best uniform {criterion}: {'/'.join(best)}; bodies {sum(counts['body'])}; "
            f"events {sum(counts['event'])}; body wins {wins}/{len(cases)}"
        )
    oracle_bodies = [min(counts["body"][index] for counts in candidates.values()) for index in range(len(cases))]
    oracle_methods = [
        min(candidates, key=lambda key: candidates[key]["event"][index])
        for index in range(len(cases))
    ]
    oracle_events = sum(candidates[key]["event"][index] for index, key in enumerate(oracle_methods))
    oracle_wins = sum(after < before for after, before in zip(oracle_bodies, baseline_bodies))
    methods = {"/".join(key): count for key, count in Counter(oracle_methods).items()}
    print(f"  Oracle body: {sum(oracle_bodies)}; body wins {oracle_wins}/{len(cases)}")
    print(
        f"  Oracle framed events: {oracle_events}; reduction vs H1 events "
        f"{1 - oracle_events / before_events:.1%}; methods {json.dumps(methods, sort_keys=True)}"
    )
    print(f"  Byte-exact candidate round trips verified: {roundtrips}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoding", choices=ENCODINGS, default="o200k_base")
    args = parser.parse_args()
    encoding = tiktoken.get_encoding(args.encoding)
    alphabet, indexes, bits = word_alphabet(encoding)
    compressors = {
        "raw": (lambda data: data, lambda data: data),
        "zlib": (partial(zlib.compress, level=9), zlib.decompress),
        "raw-deflate": (raw_deflate, partial(zlib.decompress, wbits=-15)),
        "gzip": (partial(gzip.compress, compresslevel=9, mtime=0), gzip.decompress),
        "bz2": (partial(bz2.compress, compresslevel=9), bz2.decompress),
        "lzma": (partial(lzma.compress, preset=9), lzma.decompress),
        "brotli": (partial(brotli.compress, quality=11), brotli.decompress),
    }
    renderings = {
        "base64": (lambda data: base64.b64encode(data).decode("ascii"), partial(base64.b64decode, validate=True)),
        "a85": (lambda data: base64.a85encode(data).decode("ascii"), base64.a85decode),
        "b85": (lambda data: base64.b85encode(data).decode("ascii"), base64.b85decode),
        "decimal": (lambda data: str(int.from_bytes(b"\x01" + data, "big")), lambda text: number_bytes(int(text))),
        "native-words": (
            lambda data: pack_words(data, alphabet, bits),
            lambda text: unpack_words(text, indexes, bits),
        ),
    }
    skill = Path(__file__).resolve().parent.parent
    original = json.loads((skill / "references/benchmark.json").read_text(encoding="utf-8"))["cases"]
    fresh = json.loads((skill / "references/oneoff-cases.json").read_text(encoding="utf-8"))
    print(
        f"tiktoken {version('tiktoken')}; Brotli {version('Brotli')}; encoding {args.encoding}; "
        f"native alphabet {len(alphabet)} words / {bits} bits"
    )
    benchmark(original, "original", encoding, compressors, renderings)
    benchmark(fresh, "fresh", encoding, compressors, renderings)


if __name__ == "__main__":
    main()
