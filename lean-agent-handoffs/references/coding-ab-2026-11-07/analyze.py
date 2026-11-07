#!/usr/bin/env python3
"""Validate the saved coding experiment and recompute the 70% target."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIELDS = ("input", "cached_input", "output", "reasoning_output", "total")


def read_arm(name: str, protocol: dict) -> dict:
    arm = json.loads((HERE / f"{name}.usage.json").read_text())
    if not all(arm["validation"].values()) or len(arm["sessions"]) != 2:
        raise ValueError(f"incomplete or uncontrolled arm: {name}")
    for entry in [arm, *arm["sessions"]]:
        usage = entry["usage"]
        if any(type(usage[field]) is not int or usage[field] < 0 for field in FIELDS):
            raise ValueError("invalid native counter")
        if usage["total"] != usage["input"] + usage["output"]:
            raise ValueError("total must equal input plus output")
        if usage["cached_input"] > usage["input"] or usage["reasoning_output"] > usage["output"]:
            raise ValueError("counter subset exceeds its total")
    for field in FIELDS:
        if sum(session["usage"][field] for session in arm["sessions"]) != arm["usage"][field]:
            raise ValueError("session sum mismatch")
    if sum(session["model_request_count"] for session in arm["sessions"]) != arm["model_request_count"]:
        raise ValueError("model request sum mismatch")
    quality = protocol["quality"][name]
    if not quality["acceptance_passed"] or quality["independent_acceptance"] != 12:
        raise ValueError("quality gate failed")
    if not (HERE / f"{name}.acceptance.log").read_text().endswith("\nOK\n"):
        raise ValueError("acceptance log is incomplete")
    return arm


def main() -> None:
    protocol = json.loads((HERE / "protocol.json").read_text())
    if hashlib.sha256((HERE / "acceptance.py").read_bytes()).hexdigest() != protocol["acceptance_sha256"]:
        raise ValueError("frozen acceptance harness changed")
    normal = read_arm("normal-2", protocol)
    lean = read_arm("lean-1", protocol)
    pilot = read_arm("normal-1", protocol)
    settings = {
        (entry["model"], entry["effort"])
        for arm in (normal, lean, pilot)
        for session in arm["sessions"]
        for entry in session["models_and_efforts"]
    }
    if settings != {(protocol["model"], protocol["reasoning_effort"])}:
        raise ValueError("model settings differ")
    for arm, reads, fork in ((normal, 0, "all"), (lean, 1, "none")):
        coordinator = next(session for session in arm["sessions"] if session["role"] == "coordinator")
        audit = coordinator["tool_call_audit"]
        if audit["skill_entry_read_evidence"]["count"] != reads:
            raise ValueError("activation does not match arm")
        if len(audit["spawn_calls"]) != 1 or audit["spawn_calls"][0]["fork_turns"] != fork:
            raise ValueError("delegation does not match arm")
    before, after = normal["usage"]["total"], lean["usage"]["total"]
    reduction = 1 - after / before
    print(f"Normal: {before:,} reported tokens, {normal['model_request_count']} requests")
    print(f"Automatic lean: {after:,} reported tokens, {lean['model_request_count']} requests")
    print(f"Reduction: {reduction:.4%}; meets 70%: {reduction >= 0.70}")
    uncached = [arm["usage"]["input"] - arm["usage"]["cached_input"] + arm["usage"]["output"] for arm in (normal, lean)]
    print(f"Uncached input plus output: {uncached[0]:,} -> {uncached[1]:,} ({uncached[1] / uncached[0] - 1:.1%} increase)")
    print(f"Setup pilot, excluded from matched pair: {pilot['usage']['total']:,} tokens")
    print("Both matched patches passed all 12 frozen acceptance tests.")


if __name__ == "__main__":
    main()
