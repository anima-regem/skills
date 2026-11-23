"""Render and encode the saved submissions, keeping each Blender run isolated."""

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"


def render_trial(trial_id, results, work, blender):
    trial = work / trial_id
    trial.mkdir()
    shutil.copyfile(results / f"{trial_id}.py", trial / "scene.py")
    shutil.copytree(HERE / "assets", trial / "assets")
    started = time.monotonic()
    status = "rendered"
    try:
        with (trial / "render.log").open("w") as log:
            subprocess.run([blender, "-b", "--factory-startup", "--disable-autoexec", "-t", "3",
                            "--python-exit-code", "12", "--python", str(HERE / "render.py")],
                           cwd=trial, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=360)
        frame_count = len(list((trial / "frames").glob("frame-*.png")))
        if frame_count != 48:
            raise ValueError(f"Expected 48 frames, got {frame_count}.")
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-framerate", "12",
                        "-i", str(trial / "frames/frame-%04d.png"), "-c:v", "libx264", "-crf", "23",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(results / f"{trial_id}.mp4")],
                       check=True, timeout=60)
    except (subprocess.SubprocessError, ValueError) as error:
        status = str(error).replace(str(trial), "$TRIAL").replace(str(HERE), "$BENCHMARK")
    proof = {"id": trial_id, "render_status": status, "render_seconds": round(time.monotonic() - started, 2)}
    (trial / "render.json").write_text(json.dumps(proof) + "\n")
    print(json.dumps(proof), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--results", default=HERE / "results", type=Path)
    parser.add_argument("--blender", default=shutil.which("blender") or MAC_BLENDER)
    parser.add_argument("--parallel", type=int, default=2)
    parser.add_argument("--wait", action="store_true", help="Render each submission as generation completes.")
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    order = json.loads((args.results / "manifest.json").read_text())["order"]
    pending = {f"{name}-{rep:02d}" for name, rep in order}
    deadline = time.monotonic() + 1800
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        jobs = []
        while pending:
            for trial_id in sorted(pending.copy()):
                record_path = args.results / f"{trial_id}.json"
                if record_path.exists():
                    record = json.loads(record_path.read_text())
                    pending.remove(trial_id)
                    if record["scene_produced"]:
                        jobs.append(pool.submit(render_trial, trial_id, args.results.resolve(), args.work.resolve(), args.blender))
            if not args.wait or time.monotonic() >= deadline:
                break
            if pending:
                time.sleep(1)
        for job in concurrent.futures.as_completed(jobs):
            job.result()
    if pending:
        raise SystemExit(f"No generation record for: {', '.join(sorted(pending))}")


if __name__ == "__main__":
    main()
