#!/usr/bin/env python3
"""Frozen behavioral acceptance checks; pass a candidate repository as argv[1]."""

import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(sys.argv[1]).resolve()
SCRIPT = REPOSITORY / "compact-agent-handoffs" / "scripts" / "game.py"
sys.argv = [sys.argv[0], *sys.argv[2:]]
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("acceptance_game", SCRIPT)
GAME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GAME)


def jsonl(items):
    return "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items)


def parse_jsonl(text):
    return [json.loads(line) for line in text.split("\n") if line]


def message(identifier="m1", h1="U Ready"):
    return {"id": identifier, "from": "a", "to": "b", "h1": h1}


def duplicate_member(record, key, discarded_value):
    # Keep the effective last-wins object valid so schema rejection cannot pass.
    encoded = json.dumps(record, ensure_ascii=False)
    return "{" + json.dumps(key) + ":" + json.dumps(discarded_value) + "," + encoded[1:] + "\n"


class DuplicateKeyAcceptance(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="game-acceptance-")
        self.addCleanup(self.workspace.cleanup)
        self.directory = Path(self.workspace.name)

    def run_cli(self, *args, text=""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            input=text,
            encoding="utf-8",
            capture_output=True,
            timeout=45,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def assert_duplicate(self, diagnostic, key, line=None):
        self.assertRegex(diagnostic.lower(), r"duplicate", diagnostic)
        self.assertRegex(diagnostic, r"\b" + re.escape(key) + r"\b", diagnostic)
        if line is not None:
            self.assertRegex(
                diagnostic.lower(),
                r"\bline\s*(?:[:#=]\s*)?" + str(line) + r"\b",
                diagnostic,
            )

    def assert_rejected(self, result, key, line=None):
        self.assertNotEqual(result.returncode, 0, "duplicate-key input was accepted")
        self.assertEqual(result.stdout, "", "failure published partial output")
        self.assert_duplicate(result.stderr, key, line)

    def valid_g1_stream(self, items):
        log = self.directory / "seed-g1-review.jsonl"
        result = self.run_cli("encode", "-", "--reviewer-log", log, text=jsonl(items))
        self.assert_success(result)
        return parse_jsonl(result.stdout)

    def valid_g2_stream(self, items):
        book = self.directory / "book.json"
        built = self.run_cli("book", "-", "--output", book, text=jsonl(items))
        self.assert_success(built)
        encoded = self.run_cli(
            "encode", "-", "--format", "G2", "--codebook", book,
            "--reviewer-log", self.directory / "seed-g2-review.jsonl", text=jsonl(items),
        )
        self.assert_success(encoded)
        return book, encoded.stdout

    def test_01_read_records_rejects_direct_duplicate_id(self):
        source = self.directory / "source.jsonl"
        source.write_text(duplicate_member(message(), "id", "discarded"), encoding="utf-8")
        with self.assertRaises(ValueError) as raised:
            GAME.read_records(str(source))
        self.assert_duplicate(str(raised.exception), "id", 1)

    def test_02_escaped_equivalent_id_is_rejected_in_api_and_cli(self):
        text = '{"id":"discarded","\\u0069d":"m1","from":"a","to":"b","h1":"U Ready"}\n'
        old_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO(text)
            with self.assertRaises(ValueError) as raised:
                GAME.read_records("-")
        finally:
            sys.stdin = old_stdin
        self.assert_duplicate(str(raised.exception), "id", 1)
        log = self.directory / "review.jsonl"
        result = self.run_cli("encode", "-", "--reviewer-log", log, text=text)
        self.assert_rejected(result, "id", 1)
        self.assertFalse(log.exists())

    def test_03_late_duplicate_h1_encode_publishes_neither_view(self):
        text = jsonl([message()]) + duplicate_member(message("m2"), "h1", "U Discarded")
        for mode in ("stdin", "file"):
            with self.subTest(mode=mode):
                log = self.directory / (mode + "-review.jsonl")
                source = self.directory / (mode + ".jsonl")
                source.write_text(text, encoding="utf-8")
                result = self.run_cli(
                    "encode", "-" if mode == "stdin" else source,
                    "--reviewer-log", log, text=text if mode == "stdin" else "",
                )
                self.assert_rejected(result, "h1", 2)
                self.assertFalse(log.exists())

    def test_04_book_rejects_late_duplicate_without_publishing_file(self):
        output = self.directory / "book.json"
        text = jsonl([message()]) + duplicate_member(message("m2"), "h1", "U Discarded")
        result = self.run_cli("book", "-", "--output", output, text=text)
        self.assert_rejected(result, "h1", 2)
        self.assertFalse(output.exists())

    def test_05_g1_decode_rejects_late_duplicate_without_partial_review(self):
        events = self.valid_g1_stream([message(), message("m2")])
        text = jsonl(events[:1]) + duplicate_member(events[1], "id", "discarded")
        result = self.run_cli("decode", "-", text=text)
        self.assert_rejected(result, "id", 2)

    def test_06_g2_encode_rejects_duplicate_codebook_messages(self):
        book = self.directory / "duplicated-book.json"
        book.write_text(
            '{"format":"G2-book","messages":["U Discarded"],"messages":["U Ready"]}\n',
            encoding="utf-8",
        )
        log = self.directory / "review.jsonl"
        result = self.run_cli(
            "encode", "-", "--format", "G2", "--codebook", book,
            "--reviewer-log", log, text=jsonl([message()]),
        )
        self.assert_rejected(result, "messages")
        self.assertFalse(log.exists())

    def test_07_g2_decode_rejects_duplicate_codebook_messages(self):
        book, stream = self.valid_g2_stream([message()])
        original = json.loads(book.read_text(encoding="utf-8"))
        book.write_text(duplicate_member(original, "messages", ["U Discarded"]), encoding="utf-8")
        result = self.run_cli("decode", "-", "--codebook", book, text=stream)
        self.assert_rejected(result, "messages")

    def test_08_nested_duplicates_are_detected_before_schema_validation(self):
        for nested in (
            '{"outer":{"needle":1,"needle":2}}\n',
            '{"outer":[{"needle":1,"\\u006eeedle":2}]}\n',
        ):
            with self.subTest(nested=nested):
                source = self.directory / "nested.jsonl"
                source.write_text(nested, encoding="utf-8")
                with self.assertRaises(ValueError) as raised:
                    GAME.read_records(str(source))
                self.assert_duplicate(str(raised.exception), "needle", 1)
        book = self.directory / "nested-book.json"
        book.write_text(
            '{"format":"G2-book","messages":[{"needle":1,"needle":2}]}',
            encoding="utf-8",
        )
        log = self.directory / "review.jsonl"
        result = self.run_cli(
            "encode", "-", "--format", "G2", "--codebook", book,
            "--reviewer-log", log, text=jsonl([message()]),
        )
        self.assert_rejected(result, "needle")
        self.assertFalse(log.exists())

    def test_09_existing_reviewer_evidence_is_preserved(self):
        log = self.directory / "review.jsonl"
        original = b"existing reviewer evidence\n"
        for duplicate in (False, True):
            with self.subTest(duplicate=duplicate):
                log.write_bytes(original)
                text = jsonl([message()])
                if duplicate:
                    text += duplicate_member(message("m2"), "h1", "U Discarded")
                result = self.run_cli("encode", "-", "--reviewer-log", log, text=text)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(log.read_bytes(), original)
                if duplicate:
                    self.assert_duplicate(result.stderr, "h1", 2)

    def test_10_unicode_literals_and_repeated_text_roundtrip_in_g1(self):
        h1 = 'U café/客户 \u2028 literal {"id":"x","id":"y"} \\u0069d\nS ro\n'
        items = [message("m1", h1), message("m2", h1)]
        source = self.directory / "unicode.jsonl"
        source.write_text(jsonl(items), encoding="utf-8")
        self.assertEqual(GAME.read_records(str(source)), items)
        for encoding in ("o200k_base", "cl100k_base"):
            with self.subTest(encoding=encoding):
                log = self.directory / (encoding + ".jsonl")
                encoded = self.run_cli(
                    "encode", source, "--encoding", encoding, "--reviewer-log", log,
                )
                self.assert_success(encoded)
                self.assertEqual(len(parse_jsonl(encoded.stdout)), 2)
                decoded = self.run_cli("decode", "-", text=encoded.stdout)
                self.assert_success(decoded)
                self.assertEqual(decoded.stdout, log.read_text(encoding="utf-8"))
                self.assertEqual([row["h1"] for row in parse_jsonl(decoded.stdout)], [h1, h1])

    def test_11_unicode_literals_and_repeated_text_roundtrip_in_g2(self):
        h1 = 'U café/客户 \u2028 literal {"messages":1,"messages":2} \\u0069d\nS ro\n'
        items = [message("m1", h1), message("m2", h1)]
        book, stream = self.valid_g2_stream(items)
        self.assertEqual(json.loads(book.read_text(encoding="utf-8"))["messages"], [h1])
        replay = self.run_cli("decode", "-", "--codebook", book, text=stream)
        self.assert_success(replay)
        self.assertEqual(replay.stdout, (self.directory / "seed-g2-review.jsonl").read_text(encoding="utf-8"))
        self.assertEqual([row["h1"] for row in parse_jsonl(replay.stdout)], [h1, h1])

    def test_12_g2_decode_rejects_late_duplicate_reference(self):
        book, stream = self.valid_g2_stream([message(), message("m2")])
        events = parse_jsonl(stream)
        malformed = jsonl(events[:2]) + duplicate_member(events[2], "ref", 999)
        result = self.run_cli("decode", "-", "--codebook", book, text=malformed)
        self.assert_rejected(result, "ref", 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
