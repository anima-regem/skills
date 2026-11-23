"""Build and render a submitted Blender scene with the shared review settings."""

import os
from pathlib import Path

import bpy


source = Path.cwd() / "scene.py"
namespace = {"__name__": "__main__", "__file__": str(source)}
exec(compile(source.read_bytes(), str(source), "exec"), namespace)
scene = bpy.context.scene
if scene.camera is None:
    raise RuntimeError("The submitted scene has no active camera.")
seconds = int(os.environ.get("GROUNDED_BENCHMARK_SECONDS", "4"))
fps = int(os.environ.get("GROUNDED_BENCHMARK_FPS", "12"))
frames = seconds * fps
frame_step = int(os.environ.get("GROUNDED_BENCHMARK_FRAME_STEP", "1"))
if (seconds, fps) != (4, 12):
    if frame_step != 1 or (scene.frame_start, scene.frame_end, scene.render.fps, scene.render.fps_base) != (1, frames, fps, 1.0):
        raise ValueError(f"Author scene.py at {fps} fps, FPS base 1.0, and frames 1–{frames}. The renderer needs every source frame.")
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 12
if os.environ.get("GROUNDED_BENCHMARK_DRAFT"):
    scene.eevee.taa_render_samples = 4
    scene.eevee.use_shadows = False
    scene.render.use_simplify = True
    scene.render.simplify_subdivision_render = min(scene.render.simplify_subdivision_render, 2)
    scene.render.hair_subdiv = 0
scene.frame_start = 1
scene.frame_end = frames
scene.frame_step = frame_step
scene.render.fps = fps
scene.render.fps_base = 1.0
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.use_border = False
scene.render.image_settings.media_type = "IMAGE"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(Path.cwd() / "frames" / "frame-")
if os.environ.get("RIVER_WATCH_STILL"):
    scene.frame_set(frames // 2)
    bpy.ops.render.render(write_still=True)
else:
    scene.render.use_overwrite = False
    bpy.ops.render.render(animation=True)
