"""Render and encode the saved submissions, keeping each Blender run isolated."""

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"


def render_trial(trial_id, results, work, blender, assets, draft_preview, timeout=360, frame_step=1):
    trial = work / trial_id
    trial.mkdir(exist_ok=True)
    script = results / f"{trial_id}.py"
    scene = trial / "scene.py"
    if scene.exists() and scene.read_bytes() != script.read_bytes():
        raise ValueError(f"Cannot resume {trial_id} with a different scene.")
    if not scene.exists():
        shutil.copyfile(script, scene)
        shutil.copytree(assets, trial / "assets")
    started = time.monotonic()
    status = "rendered"
    environment = os.environ.copy()
    environment["GROUNDED_BENCHMARK_FRAME_STEP"] = str(frame_step)
    if draft_preview:
        environment["GROUNDED_BENCHMARK_DRAFT"] = "1"
    frames = [trial / "frames" / f"frame-{index:04d}.png" for index in range(1, 49, frame_step)]
    try:
        if not all(frame.is_file() for frame in frames):
            with (trial / "render.log").open("a") as log:
                subprocess.run([blender, "-b", "--factory-startup", "--disable-autoexec", "-t", "3",
                                "--python-exit-code", "12", "--python", str(HERE / "render.py")],
                               cwd=trial, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=timeout)
        if not all(frame.is_file() for frame in frames):
            raise ValueError(f"Expected {len(frames)} frames, got {sum(frame.is_file() for frame in frames)}.")
        pattern = trial / "frames/frame-%04d.png"
        if frame_step != 1:
            sequence = trial / f"sequence-{frame_step}"
            sequence.mkdir(exist_ok=True)
            for index, frame in enumerate(frames, start=1):
                link = sequence / f"frame-{index:04d}.png"
                if not link.exists():
                    link.symlink_to(frame)
            pattern = sequence / "frame-%04d.png"
        temporary_video = results / f"{trial_id}.partial.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-framerate", f"12/{frame_step}",
                        "-i", str(pattern), "-c:v", "libx264", "-crf", "23",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporary_video)],
                       check=True, timeout=60)
        temporary_video.replace(results / f"{trial_id}.mp4")
    except (subprocess.SubprocessError, ValueError) as error:
        status = str(error).replace(str(trial), "$TRIAL").replace(str(HERE), "$BENCHMARK")
    proof = {"id": trial_id, "render_status": status, "render_seconds": round(time.monotonic() - started, 2)}
    (trial / "render.json").write_text(json.dumps(proof) + "\n")
    print(json.dumps(proof), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-dir", type=Path, default=HERE)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--blender", default=shutil.which("blender") or MAC_BLENDER)
    parser.add_argument("--parallel", type=int, default=2)
    parser.add_argument("--frame-step", type=int, choices=(1, 2), default=1)
    parser.add_argument("--render-timeout", type=int, default=360)
    parser.add_argument("--draft-preview", action="store_true", help="Use a uniform four-sample Eevee preview with shadows disabled.")
    parser.add_argument("--skip-existing", action="store_true", help="Keep existing review videos when resuming a render batch.")
    parser.add_argument("--wait", action="store_true", help="Render each submission as generation completes.")
    args = parser.parse_args()
    case = args.benchmark_dir.resolve()
    results = (args.results or case / "results").resolve()
    args.work.mkdir(parents=True, exist_ok=True)
    order = json.loads((results / "manifest.json").read_text())["order"]
    pending = {f"{name}-{rep:02d}" for name, rep in order}
    if args.skip_existing:
        pending = {trial_id for trial_id in pending if not (results / f"{trial_id}.mp4").is_file()}
    deadline = time.monotonic() + 1800
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
        jobs = []
        while pending:
            for trial_id in sorted(pending.copy()):
                record_path = results / f"{trial_id}.json"
                if record_path.exists():
                    record = json.loads(record_path.read_text())
                    pending.remove(trial_id)
                    if record["status"] == "complete" and record["scene_produced"]:
                        jobs.append(pool.submit(render_trial, trial_id, results, args.work.resolve(), args.blender, case / "assets", args.draft_preview, args.render_timeout, args.frame_step))
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
