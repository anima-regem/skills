"""Boundary and publication checks for the spectator token display."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import tiktoken

from game import decode_dictionary, decode_event, encode_dictionary, encode_event, make_codebook


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


class DictionaryCodecTests(unittest.TestCase):
    def setUp(self):
        self.messages = [
            {"id": "m1", "from": "a", "to": "b", "h1": 'U café/客户 \u2028 "x | y; z"\nS ro\n'},
            {"id": "m2", "from": "b", "to": "a", "h1": "C  exact  spaces  "},
        ]
        self.book = make_codebook(self.messages)

    def test_codebook_preserves_first_occurrence_and_exact_messages(self):
        repeated = {**self.messages[0], "id": "m3"}
        book = make_codebook(self.messages + [repeated])
        self.assertEqual(book, {"format": "G2-book", "messages": [item["h1"] for item in self.messages]})
        stream, reviews = encode_dictionary(self.messages + [repeated], book)
        self.assertEqual([event["ref"] for event in stream[1:]], [0, 1, 0])
        self.assertEqual([review["h1"] for review in reviews], [item["h1"] for item in self.messages] + [repeated["h1"]])
        self.assertEqual(reviews[0]["decoded"], 'Update: café/客户 \u2028 "x | y; z"\nScope: Read only.')
        self.assertEqual(reviews[1]["decoded"], "Check:  exact  spaces  ")
        self.assertEqual(decode_dictionary(stream, book), reviews)
        for event, review in zip(stream[1:], reviews):
            self.assertEqual(review["format"], "G2-review")
            self.assertEqual(review["book"], stream[0]["book"])
            for field in ("id", "from", "to", "ref"):
                self.assertEqual(review[field], event[field])

    def test_book_binding_is_independent_of_object_key_order(self):
        stream, reviews = encode_dictionary(self.messages, self.book)
        reordered = {"messages": self.book["messages"], "format": self.book["format"]}
        self.assertEqual(decode_dictionary(stream, reordered), reviews)
        changed = {**self.book, "messages": list(reversed(self.book["messages"]))}
        with self.assertRaises(ValueError):
            decode_dictionary(stream, changed)

    def test_invalid_books_and_unknown_messages_are_rejected(self):
        invalid = [
            {},
            {"format": "other", "messages": ["U Ready"]},
            {"format": "G2-book", "messages": []},
            {"format": "G2-book", "messages": "U Ready"},
            {"format": "G2-book", "messages": ["U Ready", "U Ready"]},
            {"format": "G2-book", "messages": ["X unknown"]},
            {"format": "G2-book", "messages": ["U \ud800"]},
            {"format": "G2-book", "messages": [True]},
        ]
        for book in invalid:
            with self.subTest(book=book), self.assertRaises(ValueError):
                encode_dictionary(self.messages, book)
        with self.assertRaises(ValueError):
            encode_dictionary([{**self.messages[0], "h1": "U Unknown message"}], self.book)

    def test_malformed_streams_and_references_are_rejected(self):
        stream, _ = encode_dictionary(self.messages, self.book)
        invalid = [
            [],
            [stream[0]],
            [{**stream[0], "book": "0" * 64}, *stream[1:]],
            [{**stream[0], "format": "other"}, *stream[1:]],
            [stream[0], {**stream[1], "from": False}],
            [stream[0], {**stream[1], "extra": "unexpected"}],
            [stream[0], {key: value for key, value in stream[1].items() if key != "to"}],
            [stream[0], stream[1], stream[1]],
        ]
        invalid.extend([stream[0], {**stream[1], "ref": reference}] for reference in (True, -1, 2, 0.0, None))
        for malformed in invalid:
            with self.subTest(stream=malformed), self.assertRaises(ValueError):
                decode_dictionary(malformed, self.book)

    def test_duplicate_source_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            encode_dictionary([self.messages[0], self.messages[0]], self.book)


class DictionaryCliTests(unittest.TestCase):
    run_cli = GameCliTests.run_cli

    def setUp(self):
        self.messages = [
            {"id": "m1", "from": "a", "to": "b", "h1": 'U café/客户 \u2028 "x | y; z"\nS ro\n'},
            {"id": "m2", "from": "b", "to": "a", "h1": "C  exact  spaces  "},
        ]

    def test_book_encode_and_replay_preserve_reviewer_log(self):
        with tempfile.TemporaryDirectory() as directory:
            book_path = Path(directory) / "book.json"
            log = Path(directory) / "reviewer.jsonl"
            prepared = self.run_cli("book", "-", "--output", book_path, input_text=jsonl(self.messages))
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            encoded = self.run_cli(
                "encode", "-", "--format", "G2", "--codebook", book_path,
                "--reviewer-log", log, input_text=jsonl(self.messages),
            )
            self.assertEqual(encoded.returncode, 0, encoded.stderr)
            spectator = records(encoded.stdout)
            self.assertEqual(spectator[0]["format"], "G2")
            self.assertEqual(len(spectator), len(self.messages) + 1)
            self.assertTrue(all("h1" not in event and "decoded" not in event for event in spectator))
            book = json.loads(book_path.read_text(encoding="utf-8"))
            book_path.write_text(json.dumps(book, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            replay = self.run_cli("decode", "-", "--codebook", book_path, input_text=encoded.stdout)
            self.assertEqual(replay.returncode, 0, replay.stderr)
            self.assertEqual(replay.stdout, log.read_text(encoding="utf-8"))
            self.assertEqual([event["h1"] for event in records(replay.stdout)], [item["h1"] for item in self.messages])
            unchanged_log = log.read_bytes()
            retry = self.run_cli(
                "encode", "-", "--format", "G2", "--codebook", book_path,
                "--reviewer-log", log, input_text=jsonl(self.messages),
            )
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(retry.stdout, "")
            self.assertEqual(log.read_bytes(), unchanged_log)

    def test_existing_codebook_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            book_path = Path(directory) / "book.json"
            original = b"existing codebook\n"
            book_path.write_bytes(original)
            result = self.run_cli("book", "-", "--output", book_path, input_text=jsonl(self.messages))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertEqual(book_path.read_bytes(), original)

    def test_unknown_message_and_missing_book_prevent_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            book_path = Path(directory) / "book.json"
            book_path.write_text(json.dumps(make_codebook(self.messages)), encoding="utf-8")
            log = Path(directory) / "reviewer.jsonl"
            unknown = [*self.messages, {**self.messages[0], "id": "m3", "h1": "U Unknown"}]
            for extra, dialogue in ((["--codebook", book_path], unknown), ([], self.messages)):
                result = self.run_cli(
                    "encode", "-", "--format", "G2", *extra,
                    "--reviewer-log", log, input_text=jsonl(dialogue),
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertFalse(log.exists())

    def test_late_invalid_reference_prevents_partial_reviewer_output(self):
        book = make_codebook(self.messages)
        stream, _ = encode_dictionary(self.messages, book)
        stream[-1] = {**stream[-1], "ref": -1}
        with tempfile.TemporaryDirectory() as directory:
            book_path = Path(directory) / "book.json"
            book_path.write_text(json.dumps(book), encoding="utf-8")
            result = self.run_cli("decode", "-", "--codebook", book_path, input_text=jsonl(stream))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
