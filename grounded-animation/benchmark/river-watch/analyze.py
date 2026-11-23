"""Recompute reported token totals and validate the saved comparison videos."""

import argparse
from collections import Counter
import json
import statistics
from pathlib import Path

from timing import from_manifest, probe_video


ORDER = ("raw", "physics-only", "reuse-only", "grounded", "lazy-architect", "ponytail", "caveman", "all")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path(__file__).resolve().parent / "results")
    parser.add_argument("--frame-step", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    manifest = json.loads((args.results / "manifest.json").read_text())
    timing = from_manifest(manifest)
    try:
        timing.check_frame_step(args.frame_step)
    except ValueError as error:
        parser.error(str(error))
    grouped = {name: [] for name in ORDER}
    attempts = Counter(name for name, _ in manifest["order"])
    rendered = Counter()
    print("| Run | Input | Cached input | Output | Reasoning output | Total | Video |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for name, repeat in sorted(manifest["order"], key=lambda item: (ORDER.index(item[0]), item[1])):
        trial = f"{name}-{repeat:02d}"
        row = json.loads((args.results / f"{trial}.json").read_text())
        passed = probe_video(args.results / f"{trial}.mp4", timing, args.frame_step)
        rendered[name] += passed
        video = f"[MP4](results/{trial}.mp4)" if passed else "No passing render"
        usage = row["usage"]
        if usage is None:
            print(f"| {trial} | — | — | — | — | — | {row['status']}, {video} |")
            continue
        output = usage["output_tokens"]
        total = usage["input_tokens"] + output
        uncached_plus_output = total - usage["cached_input_tokens"]
        if row["status"] == "complete":
            grouped[name].append((total, uncached_plus_output, output))
        print(f"| {trial} | {usage['input_tokens']:,} | {usage['cached_input_tokens']:,} | {output:,} | {usage['reasoning_output_tokens']:,} | {total:,} | {video} |")

    baseline = statistics.median(row[0] for row in grouped["raw"]) if grouped["raw"] else None
    print("\n| Condition | Median total | vs. raw | Median uncached input + output | Median output | Renders |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name, trials in grouped.items():
        render_count = f"{rendered[name]}/{attempts[name]}"
        if trials:
            total, uncached, output = (statistics.median(row[index] for row in trials) for index in range(3))
            delta = f"{(total / baseline - 1):+.1%}" if baseline else "—"
            print(f"| {name} | {total:,.0f} | {delta} | {uncached:,.0f} | {output:,.0f} | {render_count} |")
        elif attempts[name]:
            print(f"| {name} | — | — | — | — | {render_count} |")


if __name__ == "__main__":
    main()
