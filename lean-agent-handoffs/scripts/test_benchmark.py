"""Contract checks for benchmark scoring and the checked-in A/B evidence."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import benchmark


REFERENCES = Path(__file__).resolve().parent.parent / "references"


def load_json(name):
    return json.loads((REFERENCES / name).read_text(encoding="utf-8"))


def accepts(call, *args):
    try:
        call(*args)
    except (ValueError, UnicodeError):
        return False
    return True


class SelectedSourceTests(unittest.TestCase):
    def test_requested_definitions_and_all_imports_retain_source_text(self):
        source = (
            '"""Module context that is not requested."""\n'
            "import os as operating_system\n"
            "from pathlib import (\n"
            "    Path,\n"
            ")\n"
            "\n"
            "UNUSED = 'omit'\n"
            "VALUE = (\n"
            "    'retain spacing',  # retain this comment\n"
            "    3,\n"
            ")\n"
            "\n"
            "def unrelated():\n"
            "    return 'omit'\n"
            "\n"
            "@registered\n"
            "@configured(\n"
            "    'chosen',\n"
            ")\n"
            "def requested(value: str) -> str:\n"
            '    """Retain the body exactly."""\n'
            "    # A comment within the definition.\n"
            "    return value + ' λ'\n"
            "\n"
            "@registered\n"
            "class Widget:\n"
            "    def render(self):\n"
            "        return VALUE\n"
        )
        expected = (
            "import os as operating_system\n\n"
            "from pathlib import (\n"
            "    Path,\n"
            ")\n\n"
            "VALUE = (\n"
            "    'retain spacing',  # retain this comment\n"
            "    3,\n"
            ")\n\n"
            "@registered\n"
            "@configured(\n"
            "    'chosen',\n"
            ")\n"
            "def requested(value: str) -> str:\n"
            '    """Retain the body exactly."""\n'
            "    # A comment within the definition.\n"
            "    return value + ' λ'\n\n"
            "@registered\n"
            "class Widget:\n"
            "    def render(self):\n"
            "        return VALUE\n"
        )
        self.assertEqual(
            benchmark.selected_source(source, ["Widget", "requested", "VALUE"]),
            expected,
        )

    def test_missing_requested_definition_is_an_error(self):
        with self.assertRaises(ValueError):
            benchmark.selected_source("def present():\n    pass\n", ["present", "absent"])


class AnswerAndUsageTests(unittest.TestCase):
    def test_answer_requires_exact_boolean_values_and_keys(self):
        expected = {"allowed": True, "unsafe": False}
        self.assertTrue(benchmark.correct_answer({"unsafe": False, "allowed": True}, expected))
        invalid = (
            {"allowed": 1, "unsafe": False},
            {"allowed": True, "unsafe": 0},
            {"allowed": False, "unsafe": False},
            {"allowed": True, "unsafe": True},
            {"allowed": True},
            {"allowed": True, "unsafe": False, "extra": False},
            [("allowed", True), ("unsafe", False)],
            None,
        )
        for result in invalid:
            with self.subTest(result=result):
                self.assertFalse(benchmark.correct_answer(result, expected))

    @staticmethod
    def run_with_usage(**changes):
        usage = {
            "input_tokens": 120,
            "cached_input_tokens": 100,
            "output_tokens": 30,
            "reasoning_output_tokens": 20,
            "total_tokens": 150,
        }
        usage.update(changes)
        return {"runtime_usage": usage}

    def test_reasoning_and_cached_tokens_are_subsets_not_added_again(self):
        self.assertEqual(benchmark.native_tokens(self.run_with_usage()), 150)
        self.assertEqual(
            benchmark.native_tokens(self.run_with_usage(reasoning_output_tokens=30)), 150
        )
        self.assertEqual(
            benchmark.native_tokens(self.run_with_usage(**{
                key: 0 for key in self.run_with_usage()["runtime_usage"]
            })),
            0,
        )

    def test_impossible_usage_is_rejected(self):
        invalid = (
            {"total_tokens": 149},
            {"total_tokens": 170},  # Would double count the reasoning subset.
            {"cached_input_tokens": 121},
            {"reasoning_output_tokens": 31},
        )
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                benchmark.native_tokens(self.run_with_usage(**changes))

    def test_all_usage_counters_require_nonnegative_integers(self):
        for field in self.run_with_usage()["runtime_usage"]:
            for value in (-1, True, 1.5, "1"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    benchmark.native_tokens(self.run_with_usage(**{field: value}))

    def test_negative_counts_are_rejected_even_when_totals_balance(self):
        invalid = (
            {"input_tokens": -1, "cached_input_tokens": -1, "total_tokens": 29},
            {"output_tokens": -1, "reasoning_output_tokens": -1, "total_tokens": 119},
            {
                "input_tokens": 0,
                "cached_input_tokens": 0,
                "output_tokens": -1,
                "reasoning_output_tokens": -1,
                "total_tokens": -1,
            },
        )
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                benchmark.native_tokens(self.run_with_usage(**changes))


class FixtureEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_json("ab-fixture.json")
        cls.expected = {case["id"]: case["expected"] for case in cls.fixture["cases"]}
        cls.workspace = tempfile.TemporaryDirectory(prefix="benchmark-tests-")
        cls.addClassCleanup(cls.workspace.cleanup)
        cls.directory = Path(cls.workspace.name)
        for name, source in cls.fixture["sources"].items():
            (cls.directory / name).write_text(source, encoding="utf-8")

        def load_module(name, filename):
            spec = importlib.util.spec_from_file_location(name, cls.directory / filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        decoder = load_module("_fixture_decode", "decode.py")
        with patch.dict(sys.modules, {"decode": decoder}):
            cls.game = load_module("_fixture_game", "game.py")

    def test_source_behavior_reconstructs_the_expected_facts(self):
        game = self.game
        directory = self.directory / "publication"
        directory.mkdir()
        existing = directory / "existing.log"
        existing.write_text("original", encoding="utf-8")
        try:
            game.write_new_log(existing, "replacement")
        except FileExistsError:
            pass
        overwrites_existing = existing.read_text(encoding="utf-8") != "original"

        published = directory / "published.log"
        payload = "complete record\n" * 1000
        visible_contents = []
        real_link = game.os.link

        def observe_publication(source, destination):
            real_link(source, destination)
            visible_contents.append(Path(destination).read_text(encoding="utf-8"))

        with patch.object(game.os, "link", side_effect=observe_publication):
            game.write_new_log(published, payload)
        self.assertTrue(visible_contents, "the publication boundary was not observed")
        self.assertEqual(published.read_text(encoding="utf-8"), payload)

        failed_directory = self.directory / "failed-publication"
        failed_directory.mkdir()
        with patch.object(game.os, "link", side_effect=OSError("link unavailable")):
            with self.assertRaises(OSError):
                game.write_new_log(failed_directory / "destination.log", "content")

        book = {"format": "G2-book", "messages": ["T first", "T second"]}
        reordered_book = {"messages": book["messages"], "format": "G2-book"}
        reversed_book = {"format": "G2-book", "messages": list(reversed(book["messages"]))}
        fields = {"id", "from"}

        def read_records(text):
            path = self.directory / "records.jsonl"
            path.write_text(text, encoding="utf-8")
            return game.read_records(str(path))

        unicode_record = {"text": "one\u2028two"}
        unicode_jsonl = json.dumps(unicode_record, ensure_ascii=False) + "\n"
        self.assertEqual(read_records(unicode_jsonl), [unicode_record])
        self.assertEqual(read_records('{"id": "one"}\n'), [{"id": "one"}])
        whitespace_ids = [{"id": "one"}, {"id": " one "}]

        reconstructed = {
            "publication": {
                "overwrites_existing": overwrites_existing,
                "publishes_partial_destination": any(text != payload for text in visible_contents),
                "attempts_cleanup_after_link_failure": not any(failed_directory.iterdir()),
            },
            "hash-order": {
                "object_key_order_preserves_hash": game.codebook_hash(book) == game.codebook_hash(reordered_book),
                "reversing_distinct_messages_preserves_hash": game.codebook_hash(book) == game.codebook_hash(reversed_book),
            },
            "record-types": {
                "boolean_actor_accepted": accepts(game.validate_record, {"id": "one", "from": True}, fields),
                "lone_surrogate_accepted": accepts(game.validate_record, {"id": "one", "from": "\ud800"}, fields),
                "ref_must_be_string": not accepts(game.validate_record, {"id": "one", "ref": 7}, {"id", "ref"}),
                "unexpected_field_accepted": accepts(game.validate_record, {"id": "one", "from": "actor", "extra": "value"}, fields),
            },
            "jsonl-boundaries": {
                "u2028_splits_record": len(read_records(unicode_jsonl)) != 1,
                "blank_line_accepted": accepts(read_records, '{"id": "one"}\n\n{"id": "two"}\n'),
                "one_trailing_lf_accepted": accepts(read_records, '{"id": "one"}\n'),
            },
            "book-validation": {
                "duplicate_messages_accepted": accepts(game.validate_codebook, {"format": "G2-book", "messages": ["T same", "T same"]}),
                "plain_prose_accepted": accepts(game.validate_codebook, {"format": "G2-book", "messages": ["ordinary prose"]}),
                "empty_message_list_accepted": accepts(game.validate_codebook, {"format": "G2-book", "messages": []}),
                "scope_macro_accepted": accepts(game.validate_codebook, {"format": "G2-book", "messages": ["S ro"]}),
            },
            "id-equality": {
                "equal_ids_accepted": accepts(game.validate_unique_ids, [{"id": "one"}, {"id": "one"}]),
                "different_case_ids_accepted": accepts(game.validate_unique_ids, [{"id": "one"}, {"id": "ONE"}]),
                "normalizes_whitespace": not accepts(game.validate_unique_ids, whitespace_ids),
            },
        }
        self.assertEqual(reconstructed, self.expected)

    def test_every_individual_answer_matches_its_case(self):
        runs = load_json("ab-runs.json")
        pairs = [(run["case_id"], run["arm"]) for run in runs]
        self.assertCountEqual(pairs, [(case, arm) for case in self.expected for arm in ("normal", "lean")])
        for run in runs:
            with self.subTest(case=run["case_id"], arm=run["arm"]):
                self.assertTrue(benchmark.correct_answer(json.loads(run["raw_answer"]), self.expected[run["case_id"]]))
                benchmark.native_tokens(run)

    def test_both_batch_answers_reconstruct_all_cases(self):
        runs = load_json("ab-batches.json")
        self.assertCountEqual([run["arm"] for run in runs], ["normal", "lean"])
        for run in runs:
            result = json.loads(run["raw_answer"])
            with self.subTest(arm=run["arm"]):
                self.assertEqual(set(result), set(self.expected))
                for case, expected in self.expected.items():
                    self.assertTrue(benchmark.correct_answer(result[case], expected), case)
                benchmark.native_tokens(run)

    def test_both_context_answers_match_the_same_case(self):
        runs = load_json("ab-context.json")
        self.assertCountEqual([run["arm"] for run in runs], ["inherited", "isolated"])
        self.assertEqual(len({run["case_id"] for run in runs}), 1)
        for run in runs:
            with self.subTest(arm=run["arm"]):
                self.assertTrue(benchmark.correct_answer(json.loads(run["raw_answer"]), self.expected[run["case_id"]]))
                benchmark.native_tokens(run)


if __name__ == "__main__":
    unittest.main()
