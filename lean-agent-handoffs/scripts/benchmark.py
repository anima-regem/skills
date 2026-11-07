#!/usr/bin/env python3
"""Prepare and score controlled full-source versus selected-context handoffs."""

import argparse
import ast
import json
from pathlib import Path

import tiktoken


SKILL = Path(__file__).resolve().parent.parent
FIXTURE = SKILL / "references/ab-fixture.json"


def selected_source(source: str, names: list) -> str:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    selected = []
    found = set()
    for node in tree.body:
        node_names = set()
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            node_names.add(node.name)
        elif isinstance(node, ast.Assign):
            node_names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        if isinstance(node, (ast.Import, ast.ImportFrom)) or node_names.intersection(names):
            start = min([node.lineno] + [decorator.lineno for decorator in getattr(node, "decorator_list", [])])
            selected.append("".join(lines[start - 1:node.end_lineno]))
            found.update(node_names)
    missing = set(names) - found
    if missing:
        raise ValueError(f"missing source definitions: {sorted(missing)}")
    return "\n".join(selected)


def packet(fixture: dict, case: dict, arm: str) -> str:
    keys = ", ".join(case["expected"])
    brief = (
        "Review the supplied Python code. Use only this context, with no edits or external tools.\n"
        f"Question: {case['question']}\n"
        f"Return one JSON object with Boolean values for exactly these keys: {keys}.\n"
    )
    sections = [brief]
    for name in case["files"]:
        source = fixture["sources"][name]
        if arm == "lean":
            source = selected_source(source, case["nodes"][name])
        sections.append(f"\nSource {name}\n```python\n{source.rstrip()}\n```\n")
    return "".join(sections)


def batch_packet(fixture: dict, arm: str) -> str:
    sections = [
        "Review the supplied Python code. Use only this context, with no edits or external tools.\n"
        "Return one JSON object mapping each case ID to its requested Boolean answer object.\n"
    ]
    nodes = {}
    for case in fixture["cases"]:
        sections.append(f"\nCase {case['id']}: {case['question']}\nKeys: {', '.join(case['expected'])}.\n")
        for name, definitions in case["nodes"].items():
            nodes.setdefault(name, set()).update(definitions)
    for name, definitions in nodes.items():
        source = fixture["sources"][name]
        if arm == "lean":
            source = selected_source(source, list(definitions))
        sections.append(f"\nSource {name}\n```python\n{source.rstrip()}\n```\n")
    return "".join(sections)


def native_tokens(run: dict) -> int:
    usage = run["runtime_usage"]
    fields = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")
    if any(type(usage[name]) is not int or usage[name] < 0 for name in fields):
        raise ValueError("usage counters must be nonnegative integers")
    if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
        raise ValueError("total tokens must equal input plus output")
    if usage["cached_input_tokens"] > usage["input_tokens"] or usage["reasoning_output_tokens"] > usage["output_tokens"]:
        raise ValueError("usage subset exceeds its total")
    return usage["total_tokens"]


def correct_answer(result: dict, expected: dict) -> bool:
    return (
        isinstance(result, dict)
        and set(result) == set(expected)
        and all(type(result[key]) is bool and result[key] is value for key, value in expected.items())
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("directory", type=Path)
    report = commands.add_parser("report")
    report.add_argument("answers", type=Path)
    report.add_argument("--batches", type=Path, default=SKILL / "references/ab-batches.json")
    report.add_argument("--context", type=Path, default=SKILL / "references/ab-context.json")
    report.add_argument("--encoding", choices=("o200k_base", "cl100k_base"), default="o200k_base")
    args = parser.parse_args()
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if args.command == "prepare":
        args.directory.mkdir()
        for index, case in enumerate(fixture["cases"]):
            for arm in ("normal", "lean"):
                path = args.directory / f"{arm}-{index}.txt"
                path.write_text(packet(fixture, case, arm), encoding="utf-8")
        for arm in ("normal", "lean"):
            (args.directory / f"{arm}-batch.txt").write_text(batch_packet(fixture, arm), encoding="utf-8")
        print(args.directory)
        return

    encoding = tiktoken.get_encoding(args.encoding)

    def tokens(text: str) -> int:
        return len(encoding.encode_ordinary(text))

    runs = json.loads(args.answers.read_text(encoding="utf-8"))
    by_key = {(run["case_id"], run["arm"]): run for run in runs}
    expected_keys = {(case["id"], arm) for case in fixture["cases"] for arm in ("normal", "lean")}
    if len(by_key) != len(runs) or set(by_key) != expected_keys:
        raise ValueError("answers must contain one run per case and arm")
    setup = tokens((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    totals = {"normal": 0, "lean": 0}
    print(f"Encoding: {args.encoding}; lean setup charged per one-off handoff: {setup}")
    print("Case | Full-source tokens | Lean tokens incl setup | Reduction | Both correct")
    for case in fixture["cases"]:
        counts = {}
        correct = {}
        for arm in ("normal", "lean"):
            run = by_key[(case["id"], arm)]
            result = json.loads(run["raw_answer"])
            correct[arm] = correct_answer(result, case["expected"])
            extra = run["extra_context_tokens"][args.encoding]
            if type(extra) is not int or extra < 0:
                raise ValueError("extra context tokens must be a nonnegative integer")
            counts[arm] = (
                tokens(packet(fixture, case, arm))
                + tokens(run["dispatch"])
                + tokens(run["raw_answer"])
                + extra
            )
            if arm == "lean":
                counts[arm] += setup
            totals[arm] += counts[arm]
        passed = all(correct.values())
        reduction = 1 - counts["lean"] / counts["normal"]
        print(f"{case['id']} | {counts['normal']} | {counts['lean']} | {reduction:.1%} | {passed}")
        if not passed:
            raise ValueError(f"answer quality failed for {case['id']}")
    reduction = 1 - totals["lean"] / totals["normal"]
    print(f"Total: {totals['normal']} normal, {totals['lean']} lean ({reduction:.1%} fewer)")
    print(f"70% payload/context target reached: {reduction >= 0.70}")
    print("Scope: dispatch, supplied context, replies, expansions, and per-handoff skill setup.")
    native = {
        arm: sum(native_tokens(run) for run in runs if run["arm"] == arm)
        for arm in ("normal", "lean")
    }
    print(f"Reported native individual totals: {native}")
    print(f"Native reduction from source selection alone: {1 - native['lean'] / native['normal']:.1%}")
    batches = json.loads(args.batches.read_text(encoding="utf-8"))
    if len(batches) != 2 or {run["arm"] for run in batches} != {"normal", "lean"}:
        raise ValueError("one batch run per arm is required")
    expected = {case["id"]: case["expected"] for case in fixture["cases"]}
    for run in batches:
        result = json.loads(run["raw_answer"])
        if not isinstance(result, dict) or set(result) != set(expected) or not all(
            correct_answer(result[key], answer) for key, answer in expected.items()
        ):
            raise ValueError(f"batch answer quality failed for {run['arm']}")
        count = native_tokens(run)
        print(
            f"Native {run['arm']} batch: {count} tokens; "
            f"{1 - count / native['normal']:.1%} fewer than separate normal handoffs; "
            f"{run['model_requests']} model requests"
        )
    print("Native totals include input, cached input, and output; reasoning is an output subset.")
    print("Native totals cover child runs. Parent planning and billed currency are outside this measurement.")
    context_runs = json.loads(args.context.read_text(encoding="utf-8"))
    configurations = {
        (run["provenance"]["model"], run["provenance"]["reasoning_effort"])
        for run in runs + batches + context_runs
    }
    if len(configurations) != 1:
        raise ValueError("all observed runs must use matching model settings")
    by_arm = {run["arm"]: run for run in context_runs}
    if len(context_runs) != 2 or set(by_arm) != {"inherited", "isolated"}:
        raise ValueError("one inherited and one isolated context run are required")
    if by_arm["inherited"]["case_id"] != by_arm["isolated"]["case_id"]:
        raise ValueError("context runs must answer the same case")
    for run in context_runs:
        if not correct_answer(json.loads(run["raw_answer"]), expected[run["case_id"]]):
            raise ValueError("context-test answer quality failed")
    before = native_tokens(by_arm["inherited"])
    after = native_tokens(by_arm["isolated"])
    print(f"One-off inherited vs isolated context: {before} -> {after} ({1 - after / before:.1%} fewer)")
    uncached = {
        arm: run["runtime_usage"]["input_tokens"]
        - run["runtime_usage"]["cached_input_tokens"]
        + run["runtime_usage"]["output_tokens"]
        for arm, run in by_arm.items()
    }
    print(f"One-off uncached input plus output: {uncached} ({1 - uncached['isolated'] / uncached['inherited']:.1%} fewer)")


if __name__ == "__main__":
    main()
