# Animation benchmarks

New benchmarks use **30 seconds at native 60 fps**. Each submission authors frames 1–1,800 in Blender and renders all 1,800 source frames. The encoder preserves those frames and the verifier checks the decoded count, frame rate, and duration. Review the motion across the full 30 seconds, including the timing of deliberate holds and transitions.

Give each new case its own folder with `task.md` for the scene brief and `assets/` for any optional inputs. The runner adds delivery timing to every treatment's prompt. Run these commands from this benchmark directory with Codex CLI, Blender, Python, FFmpeg, and FFprobe available.

```bash
animation_case=/absolute/path/to/new-case
animation_run=$(mktemp -d -t animation-benchmark)
python3 river-watch/run.py --benchmark-dir "$animation_case" --work "$animation_run/trials" \
  --results "$animation_run/results" --private-scratch
python3 river-watch/render_outputs.py --benchmark-dir "$animation_case" --work "$animation_run/render" \
  --results "$animation_run/results"
python3 river-watch/analyze.py --results "$animation_run/results"
```

The [river](river-watch/README.md) and [close-up](under-the-tree/README.md) cases retain their recorded four-second settings for historical replay.
