"""Run independent Codex CLI treatments and retain provider-reported usage."""

import argparse
import concurrent.futures
import hashlib
import json
import random
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
REPO = SKILL.parent
MODEL = "gpt-6.2-sol"
EFFORT = "low"
EXTERNAL = {
    "ponytail": "https://raw.githubusercontent.com/DietrichGebert/ponytail/df9e89941d50419fd5bcf1de41e28097f1db49b2/skills/ponytail/SKILL.md",
    "caveman": "https://raw.githubusercontent.com/JuliusBrussee/caveman/2178ed6495c3c0ecd7d037e60acf3b1d0c554b97/skills/caveman/SKILL.md",
}


def section(markdown, name):
    return markdown.split(f"## {name}\n", 1)[1].split("\n## ", 1)[0].strip()


def treatments():
    entry = (SKILL / "SKILL.md").read_text()
    assets = (SKILL / "references/asset-sourcing.md").read_text()
    physics = (SKILL / "references/physics-engines.md").read_text()
    lazy = (REPO / "lazy-architect/SKILL.md").read_text()
    style = {}
    for name, url in EXTERNAL.items():
        with urllib.request.urlopen(url, timeout=20) as response:
            style[name] = response.read().decode()
    grounded = "\n\n".join((entry, assets, physics))
    return {
        "raw": "",
        "physics-only": "\n\n".join((section(entry, "Establish the scene"), section(entry, "Choose how motion is driven"), physics)),
        "reuse-only": "\n\n".join((section(entry, "Reuse existing assets"), assets)),
        "grounded": grounded,
        "lazy-architect": lazy,
        **style,
        "all": "\n\n".join((grounded, lazy, style["ponytail"], style["caveman"])),
    }


FLAGS = [
    "--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check",
    "--sandbox", "danger-full-access", "--enable", "skip_host_skill_discovery",
    "--enable", "omit_skill_descriptions", "--disable", "plugins", "--disable", "apps",
    "--disable", "hooks", "--disable", "memories", "--disable", "multi_agent",
    "--config", "project_doc_max_bytes=0", "--config", 'approval_policy="never"',
    "--config", 'web_search="cached"',
    "--config", f'model_reasoning_effort="{EFFORT}"', "--model", MODEL, "--json",
]


def isolated_cli():
    home = Path.home()
    codex = home / ".codex"
    files = [codex / name for name in ("AGENTS.md", "AGENTS.override.md")]
    directories = [home / ".agents/skills", codex / "skills", codex / "plugins/cache", REPO]
    read_rules = [f"(literal {json.dumps(str(path))})" for path in files]
    read_rules += [f"(subpath {json.dumps(str(path))})" for path in directories]
    write_rules = [f"(subpath {json.dumps(str(home / name))})" for name in ("Documents", "Projects")]
    profile = f"(version 1)(allow default)(deny file-read* {' '.join(read_rules)})(deny file-write* {' '.join(write_rules)})"
    return ["/usr/bin/sandbox-exec", "-p", profile, "codex"]


def run_trial(work, results, condition, rep, prompt, timeout):
    trial_id = f"{condition}-{rep:02d}"
    trial = work / trial_id
    trial.mkdir()
    shutil.copytree(HERE / "assets", trial / "assets")
    command = [*isolated_cli(), "exec", *FLAGS, "-C", str(trial), "-"]
    started = time.monotonic()
    status = "complete"
    with (trial / "events.jsonl").open("w") as events, (trial / "stderr.log").open("w") as stderr:
        try:
            process = subprocess.run(command, input=prompt, text=True, stdout=events, stderr=stderr, timeout=timeout)
            if process.returncode:
                status = f"exit-{process.returncode}"
        except subprocess.TimeoutExpired:
            status = "timeout"
    events = [json.loads(line) for line in (trial / "events.jsonl").read_text().splitlines() if line.startswith("{")]
    usage = [event["usage"] for event in events if event["type"] == "turn.completed"]
    tool_items = [event["item"]["type"] for event in events if event["type"] == "item.completed" and event["item"]["type"] not in ("agent_message", "reasoning", "error", "todo_list")]
    item = {
        "id": trial_id,
        "condition": condition,
        "replicate": rep,
        "status": status,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "usage": usage[-1] if usage else None,
        "tool_items_completed": tool_items,
        "scene_produced": (trial / "scene.py").is_file(),
    }
    if item["scene_produced"]:
        shutil.copyfile(trial / "scene.py", results / f"{trial_id}.py")
    (results / f"{trial_id}.json").write_text(json.dumps(item, indent=2) + "\n")
    print(json.dumps(item), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--start-replicate", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--only", nargs="+")
    args = parser.parse_args()
    work, results = args.work.resolve(), args.results.resolve()
    work.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    task = (HERE / "task.md").read_text()
    guidance = treatments()
    order = [(name, i) for i in range(args.start_replicate, args.start_replicate + args.repeats) for name in (args.only or guidance)]
    random.Random(6841).shuffle(order)
    prompts = {name: task + (f"\n## Skill guidance for this trial\n\n{guidance[name]}\n" if guidance[name] else "") for name, _ in order}
    manifest = {
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "codex_cli": subprocess.check_output(["codex", "--version"], text=True).strip(),
        "flags": FLAGS,
        "isolation": "macOS Seatbelt blocks global AGENTS, installed skill directories, plugin cache, and the skills repository",
        "order": order,
        "parallel": args.parallel,
        "timeout_seconds": args.timeout,
        "prompt_sha256": {name: hashlib.sha256(prompt.encode()).hexdigest() for name, prompt in prompts.items()},
        "prompt_bytes": {name: len(prompt.encode()) for name, prompt in prompts.items()},
        "asset_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((HERE / "assets").iterdir()) if path.is_file()},
        "external_skills": EXTERNAL,
    }
    (results / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = [pool.submit(run_trial, work, results, name, rep, prompts[name], args.timeout) for name, rep in order]
        for future in concurrent.futures.as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
