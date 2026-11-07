#!/usr/bin/env python3
"""Expand H1 handoffs into labeled text using only the standard library."""

import argparse
import sys
from pathlib import Path


FIELDS = {
    "T": "Task",
    "U": "Update",
    "D": "Done",
    "B": "Blocked",
    "Q": "Ask",
    "S": "Scope",
    "C": "Check",
    "N": "Next",
}


def decode(message: str) -> str:
    """Validate the entire message before returning its expanded fields."""
    lines = message.split("\n")
    if lines[-1] == "":
        lines.pop()
    if not lines:
        raise ValueError("empty H1 message")

    decoded = []
    for number, line in enumerate(lines, start=1):
        code, separator, content = line.partition(" ")
        if code not in FIELDS or not separator or not content.strip():
            raise ValueError(f"line {number}: expected a known H1 code, a space, and text")
        if code == "S" and content == "ro":
            content = "Read only."
        decoded.append(f"{FIELDS[code]}: {content}")
    return "\n".join(decoded)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="UTF-8 H1 file, or - for stdin")
    args = parser.parse_args()
    try:
        message = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
        expanded = decode(message)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"decode: {error}\n")
    print(expanded)


if __name__ == "__main__":
    main()
