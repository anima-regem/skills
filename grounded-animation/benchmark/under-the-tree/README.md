# Under the Tree benchmark

A four-second close-up of a man watching leaves fall at the edge of a field. This reuses the river benchmark's eight conditions and model. The new brief puts the eyes and mouth in the foreground and asks for one breeze to affect both airborne leaves and rooted plants. The submitted scenes target 12 fps. The shared review clips sample six frames per second.

- [Scene script and shared brief](task.md)
- [Directed close-up still](hero.png) · [Blender source for the still](hero.py)
- [All-skills example at 12 fps](full-speed-all-02.mp4)
- [Results and clips](RESULTS.md)
- [Research notes and asset credits](research-notes.md)
- [Shared optional assets](assets/README.md)
- [Model settings, run order, and input hashes](results/manifest.json)

## Reproduce

Run from this directory on macOS with the authenticated Codex CLI, Blender 5.2, Python, and FFmpeg. The usage analysis reads saved results and makes no model calls.

```bash
python3 ../river-watch/analyze.py --results results --frame-step 2
```

Start a fresh benchmark with the same shared runner. Fresh model runs and cache usage can differ.

```bash
tree_run=$(mktemp -d -t under-the-tree)
python3 ../river-watch/run.py --benchmark-dir . --work "$tree_run/trials" \
  --results "$tree_run/results" --parallel 6 --timeout 480 --private-scratch
python3 ../river-watch/render_outputs.py --benchmark-dir . --work "$tree_run/render" \
  --results "$tree_run/results" --parallel 2 --draft-preview --frame-step 2 --render-timeout 900
python3 ../river-watch/analyze.py --results "$tree_run/results" --frame-step 2
```

To rebuild the separate 1280×720 still, run `Blender -b --factory-startup --disable-autoexec -P hero.py` with the supplied assets beside the script.

Recorded follow-up runs used `--repeats 1 --start-replicate 3 --timeout 600 --only CONDITION`. Save those to a separate results directory so the original manifest remains available. The published combined manifest records every attempt.
