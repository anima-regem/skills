# Research notes

## What the scene tests

The scene script was frozen before generation. It asks for a pensive face in tight three-quarter close-up, a brief gust, eye-led tracking of a falling leaf, and a blink as the gust fades. The field and bark must establish the place without crowding the face.

The same eight [treatments from the river benchmark](../river-watch/research-notes.md#what-was-varied) use the same `gpt-6.2-sol` model and low reasoning setting. Submitted scenes target 640×360 and 12 fps over frames 1–48. The close-up is an original scene with game cinematics as a visual reference. The [directed still](hero.png) uses its own staging and 56 Eevee samples at 1280×720. It is excluded from the measurements.

## Shared assets and license

**Einar Rig (CC-BY) Blender Foundation | studio.blender.org.** The benchmark asset is derived from Blender Studio's Einar v1 release, supplied under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source ZIP had SHA-256 `3cbb5a1dd9ffd3ca39edab420a83ea7f7db337b435a78ef27a0c87ff3e6977f7`. The packed derivative retained the studio's native facial controls and groom, trimmed out-of-frame parts and reduced maps. Its eyebrow, eyelid, gaze, jaw, and mouth-corner controls were tested in headless Blender. [Einar release](https://studio.blender.org/characters/einar/v1/) · [Layered facial sculpting](https://studio.blender.org/blog/layered-sculpting-for-einar/)

The optional oak textures, interactive-ready grass geometry, and autumn meadow HDRI come from Poly Haven under CC0. The grass import was exercised in headless Blender. The assets are available to every treatment, and the brief leaves their use optional. Starting from a supplied rig tests adaptation and expression. Asset discovery from a blank scene is a separate task. [Environment sources](assets/environment/README.md)

## Isolation, quality and token accounting

As before, host skill files, global instructions, the plugin cache, and the repository are blocked inside the trial processes. The close-up benchmark also blocks access to other trial directories and writes to fixed paths in shared `/tmp`. A setup attempt blocked the shell's own temporary files used for multiline commands. It was stopped and excluded. The measured profile permits the shell's unique temporary names. Probes verified writes in a trial's own directory and denial of a fixed shared path. The runner records the requested skill guidance and asset hashes, with complete media generated outside the measured turns. The timeout is 480 seconds per attempt.

Review the facial change, tight framing and context, the relationship between leaf and field motion, and visible continuity. Short reviews and two completed runs per condition cannot isolate modest quality differences. The scene does not test a detailed plant or airflow simulation.

Initial shared-renderer probes spent tens of seconds per frame on complex close-up scenes. A live Blender sample found the renderer waiting on a Metal read during the Eevee shadow pass. Standardized review clips use Blender 5.2.2, four Eevee samples, a subdivision cap, and shadows disabled. They encode the 24 odd frames from the source timeline at 6 fps. One [all-skills example](full-speed-all-02.mp4) also retains the original 48-frame draft render. Candidate Python is kept as submitted. The preview limits comparisons of hair fidelity, shadowing, final-grade image quality, and short movements between samples such as a blink.

Token counts come from completed Codex turns. The input count includes cached input, and the output count includes reasoning output. Uncached input plus output is shown separately. These are token counts, with no session billing estimate.

The first pass made 16 attempts with a 480-second limit. Five follow-up attempts reused the identical prompt and asset hashes with a 600-second limit. One replacement each completed for Physics only, Reuse only, and Lazy Architect. The full Grounded Animation and all-skills replacements timed out, leaving one completed count for each. A timeout can retain a draft script, and it provides no completed-turn usage count. Median totals use completed runs only, so the table shows the sample size alongside each condition.
