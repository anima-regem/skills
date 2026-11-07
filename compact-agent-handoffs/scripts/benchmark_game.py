#!/usr/bin/env python3
"""Measure the G1 spectator representation against the same H1 messages."""

import argparse
import json
from pathlib import Path

import tiktoken

from game import ENCODINGS, decode_event, encode_event, json_line


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoding", choices=ENCODINGS, default="o200k_base")
    args = parser.parse_args()
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


if __name__ == "__main__":
    main()
