#!/usr/bin/env python3
"""Render H1 game dialogue as token IDs and retain decoded reviewer records."""

import argparse
import json
import os
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import tiktoken

from decode import decode


ENCODINGS = ("o200k_base", "cl100k_base")
TOKENIZER_VERSION = version("tiktoken")
INPUT_FIELDS = {"id", "from", "to", "h1"}
EVENT_FIELDS = {"format", "tokenizer", "encoding", "id", "from", "to", "tokens"}


def json_line(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"


def validate_record(record: dict, fields: set) -> None:
    if not isinstance(record, dict) or set(record) != fields:
        raise ValueError(f"record must contain exactly {sorted(fields)}")
    for name in fields - {"tokens"}:
        value = record[name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonempty string")
        value.encode("utf-8", errors="strict")


def encode_event(record: dict, encoding_name: str) -> dict:
    validate_record(record, INPUT_FIELDS)
    decode(record["h1"])
    if encoding_name not in ENCODINGS:
        raise ValueError("unsupported encoding")
    encoding = tiktoken.get_encoding(encoding_name)
    return {
        "format": "G1",
        "tokenizer": TOKENIZER_VERSION,
        "encoding": encoding_name,
        "id": record["id"],
        "from": record["from"],
        "to": record["to"],
        "tokens": encoding.encode_ordinary(record["h1"]),
    }


def decode_event(event: dict) -> dict:
    validate_record(event, EVENT_FIELDS)
    if event["format"] != "G1" or event["tokenizer"] != TOKENIZER_VERSION:
        raise ValueError(f"expected G1 with tiktoken {TOKENIZER_VERSION}")
    if event["encoding"] not in ENCODINGS:
        raise ValueError("unsupported encoding")
    encoding = tiktoken.get_encoding(event["encoding"])
    token_ids = event["tokens"]
    if not isinstance(token_ids, list) or not token_ids:
        raise ValueError("tokens must be a nonempty list of integer IDs")
    if any(type(token) is not int or token < 0 or token >= encoding.n_vocab for token in token_ids):
        raise ValueError("tokens contain an invalid integer ID")
    try:
        h1 = encoding.decode(token_ids, errors="strict")
    except (KeyError, UnicodeError) as error:
        raise ValueError("tokens contain an unknown ID or invalid UTF-8") from error
    if encoding.encode_ordinary(h1) != token_ids:
        raise ValueError("tokens must be the ordinary canonical encoding of the H1 text")
    expanded = decode(h1)
    return {
        "format": "G1-review",
        "tokenizer": event["tokenizer"],
        "encoding": event["encoding"],
        "id": event["id"],
        "from": event["from"],
        "to": event["to"],
        "h1": h1,
        "decoded": expanded,
    }


def read_records(source: str) -> list:
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    if not lines:
        raise ValueError("empty dialogue")
    records = []
    for number, line in enumerate(lines, start=1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"line {number}: invalid JSON") from error
    return records


def write_new_log(path: Path, content: str) -> None:
    """Publish a complete log while preserving any existing destination."""
    staged = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False)
    staged_path = Path(staged.name)
    try:
        with staged:
            staged.write(content)
            staged.flush()
            os.fsync(staged.fileno())
        os.link(staged_path, path)
    finally:
        staged_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    encoder = commands.add_parser("encode", help="write reviewer log, then emit spectator JSONL")
    encoder.add_argument("input", help="UTF-8 dialogue JSONL file, or - for stdin")
    encoder.add_argument("--encoding", choices=ENCODINGS, default="o200k_base")
    encoder.add_argument("--reviewer-log", required=True, type=Path)
    decoder = commands.add_parser("decode", help="regenerate reviewer JSONL from spectator JSONL")
    decoder.add_argument("input", help="UTF-8 spectator JSONL file, or - for stdin")
    args = parser.parse_args()
    try:
        records = read_records(args.input)
        if args.command == "encode":
            events = [encode_event(record, args.encoding) for record in records]
            reviews = [decode_event(event) for event in events]
            if [review["h1"] for review in reviews] != [record["h1"] for record in records]:
                raise ValueError("token encoding failed to preserve input H1")
        else:
            events = records
            reviews = [decode_event(event) for event in events]
        ids = [review["id"] for review in reviews]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate message IDs in dialogue")
        review_log = "".join(json_line(review) for review in reviews)
        if args.command == "encode":
            write_new_log(args.reviewer_log, review_log)
            output = "".join(json_line(event) for event in events)
        else:
            output = review_log
        sys.stdout.write(output)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"game: {error}\n")


if __name__ == "__main__":
    main()
