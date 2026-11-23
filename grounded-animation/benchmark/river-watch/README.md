# River watcher benchmark

Eight conditions and one brief. Each condition produced two completed Blender scenes of a person watching a river flow. One additional attempt timed out. We saved the model's Python, the CLI token counts, and the common-renderer MP4 for each completed scene.

- [Results and videos](RESULTS.md)
- [Research notes and treatment definitions](research-notes.md)
- [Shared task](task.md)
- [Run order, model settings, and input hashes](results/manifest.json)

## Reproduce

Recompute the saved token tables and check video format with Python and FFprobe. This makes no model calls.

```bash
python3 analyze.py
```

Run a fresh comparison on macOS with an authenticated Codex CLI, Blender 5.2, Python, and FFmpeg. Run the commands from this folder. The runner uses macOS Seatbelt to keep host skill files out of the trial context. Fresh runs can differ.

```bash
river_run=$(mktemp -d -t river-watch)
python3 run.py --work "$river_run/trials" --results "$river_run/results" --parallel 6
python3 render_outputs.py --work "$river_run/render" --results "$river_run/results"
python3 analyze.py --results "$river_run/results"
```

The measured run also used a fresh Grounded Animation replicate with `--only grounded --repeats 1 --start-replicate 3 --timeout 480 --parallel 1` after an initial timeout. Save that retry to a separate results directory to preserve the original manifest.
