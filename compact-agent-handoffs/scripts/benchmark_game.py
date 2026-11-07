#!/usr/bin/env python3
"""Measure G1 and shared-codebook G2 game representations against H1."""

import argparse
import json
from pathlib import Path

import tiktoken

from game import (
    ENCODINGS,
    decode_dictionary,
    decode_event,
    encode_dictionary,
    encode_event,
    json_line,
    make_codebook,
)


def benchmark_dictionary(cases: list, encoding, repetitions: list) -> None:
    def tokens(text: str) -> int:
        return len(encoding.encode_ordinary(text))

    seed = [
        {"id": case["id"], "from": "/root/worker", "to": "/root", "h1": case["h1"]}
        for case in cases
    ]
    book = make_codebook(seed)
    book_tokens = tokens(json_line(book))
    print(f"G2 codebook tokens, including format and all exact messages: {book_tokens}")
    print("Cycles | Messages | H1 bodies | Ref bodies | H1 events | G2 warm | G2 cold | Cold reduction")
    for cycles in repetitions:
        records = [
            {**record, "id": f"{record['id']}:{cycle}"}
            for cycle in range(cycles)
            for record in seed
        ]
        stream, reviews = encode_dictionary(records, book)
        replay = decode_dictionary(stream, book)
        if reviews != replay or [review["h1"] for review in replay] != [record["h1"] for record in records]:
            raise ValueError("G2 reviewer replay did not preserve the dialogue")
        expected = [case["decoded"] for _ in range(cycles) for case in cases]
        if [review["decoded"] for review in reviews] != expected:
            raise ValueError("G2 expanded reviewer text differs from fixture")
        plain = sum(tokens(json_line(record)) for record in records)
        header_tokens = tokens(json_line(stream[0]))
        warm = sum(tokens(json_line(record)) for record in stream)
        cold = warm + book_tokens
        bodies = sum(tokens(record["h1"]) for record in records)
        refs = sum(tokens(str(record["ref"])) for record in stream[1:])
        print(
            f"{cycles} | {len(records)} | {bodies} | {refs} | {plain} | "
            f"{warm} | {cold} | {1 - cold / plain:.1%}"
        )
        reviewer_bytes = sum(len(json_line(review).encode("utf-8")) for review in reviews)
        reviewer_tokens = sum(tokens(json_line(review)) for review in reviews)
        print(
            f"G2 {cycles} cycles: {len(replay)} exact replays; header {header_tokens} tokens; "
            f"reviewer log {reviewer_tokens} tokens / {reviewer_bytes} UTF-8 bytes"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoding", choices=ENCODINGS, default="o200k_base")
    parser.add_argument("--cycles", nargs="+", type=int, default=[1, 2, 10])
    args = parser.parse_args()
    if any(cycles < 1 for cycles in args.cycles):
        parser.error("cycles must be positive")
    encoding = tiktoken.get_encoding(args.encoding)
    skill = Path(__file__).resolve().parent.parent
    fixture = json.loads((skill / "references/benchmark.json").read_text(encoding="utf-8"))
    totals = {name: 0 for name in ("h1", "ids", "plain", "spectator", "reviewer")}
    storage = {name: 0 for name in totals}

    print(f"Encoding: {args.encoding}")
    print("Case | H1 body | ID array | H1 event | Spectator event | Reviewer event")
    for case in fixture["cases"]:
        source = {"id": case["id"], "from": "/root/worker", "to": "/root", "h1": case["h1"]}
        event = encode_event(source, args.encoding)
        review = decode_event(event)
        if review["h1"] != source["h1"] or review["decoded"] != case["decoded"]:
            raise ValueError(f"round-trip mismatch for {case['id']}")
        representations = {
            "h1": source["h1"],
            "ids": json.dumps(event["tokens"], separators=(",", ":")),
            "plain": json_line(source),
            "spectator": json_line(event),
            "reviewer": json_line(review),
        }
        counts = {}
        for name, text in representations.items():
            counts[name] = len(encoding.encode_ordinary(text))
            totals[name] += counts[name]
            storage[name] += len(text.encode("utf-8"))
        print(f"{case['id']} | " + " | ".join(str(counts[name]) for name in totals))

    print("Total tokens: " + json.dumps(totals))
    print("Total UTF-8 bytes: " + json.dumps(storage))
    print(f"Numeric payload / H1 body: {totals['ids'] / totals['h1']:.2f}x")
    print(f"Spectator / H1 event: {totals['spectator'] / totals['plain']:.2f}x")
    print(f"Spectator plus reviewer tokens: {totals['spectator'] + totals['reviewer']}")
    print(f"Exact H1 and expanded reviewer round trips verified: {len(fixture['cases'])}")
    benchmark_dictionary(fixture["cases"], encoding, args.cycles)


if __name__ == "__main__":
    main()
