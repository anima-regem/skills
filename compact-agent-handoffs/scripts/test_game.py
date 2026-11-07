"""Boundary and publication checks for the spectator token display."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tiktoken

from game import decode_event, encode_event


SCRIPT = Path(__file__).with_name("game.py")


def jsonl(records):
    return "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)


def records(text):
    return [json.loads(line) for line in text.split("\n") if line]


class GameCodecTests(unittest.TestCase):
    def setUp(self):
        self.message = {
            "id": "m1",
            "from": "/root/cache",
            "to": "/root",
            "h1": 'U café/客户 \u2028 "miss | busy; retry"\nS ro\n',
        }

    def test_unicode_and_literals_round_trip_in_both_encodings(self):
        for encoding in ("o200k_base", "cl100k_base"):
            with self.subTest(encoding=encoding):
                spectator = encode_event(self.message, encoding)
                self.assertEqual(spectator["format"], "G1")
                self.assertEqual(spectator["encoding"], encoding)
                self.assertNotIn("h1", spectator)
                self.assertNotIn("decoded", spectator)
                reviewer = decode_event(spectator)
                self.assertEqual(reviewer["format"], "G1-review")
                self.assertEqual(reviewer["h1"], self.message["h1"])
                self.assertEqual(
                    reviewer["decoded"],
                    'Update: café/客户 \u2028 "miss | busy; retry"\nScope: Read only.',
                )
                self.assertNotIn("tokens", reviewer)
                for key in ("id", "from", "to", "encoding", "tokenizer"):
                    self.assertEqual(reviewer[key], spectator[key])

    def test_input_fields_and_h1_are_validated(self):
        invalid = [
            {**self.message, "id": ""},
            {**self.message, "from": True},
            {**self.message, "to": 7},
            {**self.message, "h1": "plain prose"},
            {**self.message, "h1": "U valid\nX unknown"},
            {**self.message, "extra": "unexpected"},
            {key: value for key, value in self.message.items() if key != "to"},
        ]
        for message in invalid:
            with self.subTest(message=message):
                with self.assertRaises(ValueError):
                    encode_event(message, "o200k_base")

    def test_lone_surrogates_are_rejected_before_tokenizer_replacement(self):
        with self.assertRaises(ValueError):
            encode_event({**self.message, "h1": "U \ud800"}, "o200k_base")

    def test_invalid_token_ids_and_metadata_are_rejected(self):
        event = encode_event(self.message, "o200k_base")
        encoding = tiktoken.get_encoding("o200k_base")
        changes = [
            {"tokens": [True]},
            {"tokens": [-1]},
            {"tokens": [1.0]},
            {"tokens": [encoding.n_vocab]},
            {"tokens": "1 2 3"},
            {"format": "unknown"},
            {"encoding": "unknown"},
            {"tokenizer": "unknown-version"},
        ]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    decode_event({**event, **change})

    def test_invalid_utf8_tokens_are_rejected(self):
        event = encode_event(self.message, "o200k_base")
        encoding = tiktoken.get_encoding("o200k_base")
        invalid_byte = encoding.encode_single_token(b"\xff")
        with self.assertRaises(ValueError):
            decode_event({**event, "tokens": [invalid_byte]})

    def test_special_and_noncanonical_token_sequences_are_rejected(self):
        event = encode_event(self.message, "o200k_base")
        encoding = tiktoken.get_encoding("o200k_base")
        ordinary = encoding.encode_ordinary("U hello")
        split_bytes = [encoding.encode_single_token(bytes([byte])) for byte in b"U hello"]
        self.assertNotEqual(split_bytes, ordinary)
        special = encoding.encode_ordinary("U ") + [encoding.eot_token]
        for token_ids in (split_bytes, special):
            with self.subTest(token_ids=token_ids):
                with self.assertRaises(ValueError):
                    decode_event({**event, "tokens": token_ids})


class GameCliTests(unittest.TestCase):
    def run_cli(self, *args, input_text):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            input=input_text,
            encoding="utf-8",
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_spectator_output_replays_to_identical_reviewer_log(self):
        messages = [
            {"id": "m1", "from": "a", "to": "b", "h1": 'U café/客户 \u2028 "x | y; z"'},
            {"id": "m2", "from": "b", "to": "a", "h1": "D Fixed\nC 8 passed; 1 failed"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "reviewer.jsonl"
            result = self.run_cli("encode", "-", "--reviewer-log", log, input_text=jsonl(messages))
            self.assertEqual(result.returncode, 0, result.stderr)
            spectator = records(result.stdout)
            self.assertEqual(len(spectator), len(messages))
            self.assertEqual([event["id"] for event in spectator], ["m1", "m2"])
            replay = self.run_cli("decode", "-", input_text=result.stdout)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual(replay.stdout, log.read_text(encoding="utf-8"))
            self.assertEqual([event["h1"] for event in records(replay.stdout)], [item["h1"] for item in messages])

    def test_late_malformed_input_publishes_neither_view(self):
        valid = {"id": "m1", "from": "a", "to": "b", "h1": "U Ready"}
        for suffix in ('{"invalid"', jsonl([{**valid, "id": "m2", "h1": "X unknown"}])):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                log = Path(directory) / "reviewer.jsonl"
                result = self.run_cli("encode", "-", "--reviewer-log", log, input_text=jsonl([valid]) + suffix)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertFalse(log.exists())

    def test_file_input_matches_stdin(self):
        message = {"id": "m1", "from": "a", "to": "b", "h1": "U café/客户 \u2028 Ready"}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            source.write_text(jsonl([message]), encoding="utf-8")
            file_result = self.run_cli(
                "encode", source, "--reviewer-log", Path(directory) / "file-review.jsonl", input_text=""
            )
            stdin_result = self.run_cli(
                "encode", "-", "--reviewer-log", Path(directory) / "stdin-review.jsonl", input_text=jsonl([message])
            )
            self.assertEqual(file_result.returncode, 0, file_result.stderr)
            self.assertEqual(stdin_result.returncode, 0, stdin_result.stderr)
            self.assertEqual(file_result.stdout, stdin_result.stdout)

    def test_duplicate_message_ids_are_rejected(self):
        message = {"id": "m1", "from": "a", "to": "b", "h1": "U Ready"}
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "reviewer.jsonl"
            result = self.run_cli("encode", "-", "--reviewer-log", log, input_text=jsonl([message, message]))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse(log.exists())

    def test_existing_reviewer_log_is_preserved(self):
        message = {"id": "m1", "from": "a", "to": "b", "h1": "U Ready"}
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "reviewer.jsonl"
            original = b"existing reviewer evidence\n"
            log.write_bytes(original)
            result = self.run_cli("encode", "-", "--reviewer-log", log, input_text=jsonl([message]))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(log.read_bytes(), original)

    def test_reviewer_log_write_failure_prevents_spectator_output(self):
        message = {"id": "m1", "from": "a", "to": "b", "h1": "U Ready"}
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "missing" / "reviewer.jsonl"
            result = self.run_cli("encode", "-", "--reviewer-log", log, input_text=jsonl([message]))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse(log.exists())

    def test_decode_batch_errors_do_not_emit_partial_reviewer_output(self):
        valid = encode_event({"id": "m1", "from": "a", "to": "b", "h1": "U Ready"}, "o200k_base")
        invalid = {**valid, "id": "m2", "tokens": [-1]}
        result = self.run_cli("decode", "-", input_text=jsonl([valid, invalid]))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
