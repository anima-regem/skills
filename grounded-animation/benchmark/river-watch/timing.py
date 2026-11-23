"""Delivery timing shared by benchmark generation, rendering, and verification."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Timing:
    seconds: int
    fps: int

    @property
    def frames(self):
        return self.seconds * self.fps

    def check_frame_step(self, frame_step):
        if frame_step != 1 and self != LEGACY:
            raise ValueError("New benchmarks require a render for every source frame. Use --frame-step 1.")


STANDARD = Timing(seconds=30, fps=60)
LEGACY = Timing(seconds=4, fps=12)
HERE = Path(__file__).resolve().parent


def for_case(case):
    return LEGACY if case.resolve() in (HERE, HERE.with_name("under-the-tree")) else STANDARD


def from_manifest(manifest):
    return Timing(**manifest["delivery_timing"]) if "delivery_timing" in manifest else LEGACY


def probe_video(path, timing, frame_step):
    if not path.is_file():
        return False
    inspection = subprocess.run([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration", "-of", "json", str(path),
    ], capture_output=True, text=True)
    if inspection.returncode or inspection.stderr:
        return False
    streams = json.loads(inspection.stdout).get("streams", [])
    fps = f"{timing.fps // frame_step}/1"
    return len(streams) == 1 and all(streams[0].get(key) == value for key, value in {
        "width": 640,
        "height": 360,
        "r_frame_rate": fps,
        "avg_frame_rate": fps,
        "nb_read_frames": str(timing.frames // frame_step),
        "duration": f"{timing.seconds:.6f}",
    }.items())
