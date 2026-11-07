#!/usr/bin/env python3
"""Compare the frozen previous skill's handoffs with decoded and H1 text."""

import argparse
import json
from pathlib import Path

import tiktoken

from decode import decode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoding", default="o200k_base", choices=("o200k_base", "cl100k_base"))
    args = parser.parse_args()
    skill = Path(__file__).resolve().parent.parent
    fixture = json.loads((skill / "references/benchmark.json").read_text(encoding="utf-8"))
    encoding = tiktoken.get_encoding(args.encoding)

    def tokens(message: str) -> int:
        return len(encoding.encode_ordinary(message))

    rows = []
    for case in fixture["cases"]:
        expanded = decode(case["h1"])
        if expanded != case["decoded"]:
            raise ValueError(f"decoder mismatch for {case['id']}")
        rows.append({
            "id": case["id"],
            "set": case["set"],
            "current": tokens(case["current"]),
            "expanded": tokens(expanded),
            "h1": tokens(case["h1"]),
        })

    print(f"Encoding: {args.encoding}")
    print("Case | Previous skill | Expanded H1 | H1")
    for row in rows:
        print(f"{row['id']} | {row['current']} | {row['expanded']} | {row['h1']}")

    for name in ("original", "evaluation", "all"):
        selected = rows if name == "all" else [row for row in rows if row["set"] == name]
        before = sum(row["current"] for row in selected)
        expanded = sum(row["expanded"] for row in selected)
        after = sum(row["h1"] for row in selected)
        print(
            f"{name}: {before} previous, {expanded} expanded, {after} H1 "
            f"({1 - after / before:.1%} fewer vs previous)"
        )

    setup_before = tokens(fixture["baseline_skill"])
    setup_after = tokens((skill / "SKILL.md").read_text(encoding="utf-8"))
    saved = sum(row["current"] - row["h1"] for row in rows)
    extra_setup = max(0, setup_after - setup_before)
    print(f"Instructions per load: {setup_before} previous, {setup_after} H1")
    total_before = setup_before + sum(row["current"] for row in rows)
    total_after = setup_after + sum(row["h1"] for row in rows)
    print(f"One load plus fixture payloads: {total_before} previous, {total_after} H1")
    if saved > 0:
        print(f"Handoffs to offset extra setup vs previous: {extra_setup * len(rows) // saved + 1}")
        print(f"Handoffs to offset a new H1 load vs already-loaded previous: {setup_after * len(rows) // saved + 1}")
    print(f"Decoder fixtures verified: {len(rows)}")


if __name__ == "__main__":
    main()
