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
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 12
scene.frame_start = 1
scene.frame_end = 48
scene.frame_step = 1
scene.render.fps = 12
scene.render.fps_base = 1.0
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.use_border = False
scene.render.image_settings.media_type = "IMAGE"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(Path.cwd() / "frames" / "frame-")
if os.environ.get("RIVER_WATCH_STILL"):
    scene.frame_set(24)
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
