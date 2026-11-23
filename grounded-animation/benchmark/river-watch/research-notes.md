# Research notes

## What was varied

| Treatment | Guidance appended to the shared brief |
| --- | --- |
| Raw | None |
| Physics only | Grounded Animation's scene and motion-driver sections plus the physics reference |
| Reuse only | Grounded Animation's sourcing section plus the asset and motion reference |
| Grounded Animation | The entry point and both references, preloaded |
| Lazy Architect | The repository's Lazy Architect entry point |
| Ponytail | The pinned upstream skill in its default mode |
| Caveman | The pinned upstream entry point in its default mode |
| All | Grounded Animation, Lazy Architect, Ponytail, and Caveman |

These are single-agent creation trials. Lean Agent Handoffs was applied to benchmark preparation. Glazing Perfectionist applies to identity and type work, and the animation brief contained neither. All conditions shared the same optional inputs and public reference access. Full Grounded Animation was deliberately preloaded, so the comparison includes the cost of both references. It does not estimate lazy reference loading in ordinary use.

## Isolation and accounting

Transcripts from the first setup attempt showed that disabling host skill discovery still left global `AGENTS.md` in the prompt. Several agents explicitly loaded Lazy Architect. The attempt was stopped and excluded. A second setup probe used an outer macOS Seatbelt profile to block reads of global instructions, installed skills, the plugin cache, and the skills repository. Its saved turn contained no global instructions or skill catalog, and its shell tool could write in the trial folder. The measured runner uses that profile. No host configuration was edited.

The profile isolates skill context. Shell commands still share the host's general temporary directory. Both all-skills runs used the same temporary filename while inspecting the identical local humanoid. The renderer built each submitted source in a separate folder with the shared asset pack, so this detail can affect the probe sequence and token counts. Rendering runs locally and executes Python generated for the benchmark.

Use the CLI's completed-turn usage fields. Input includes cached input, and output includes reasoning output. Add input and output for total provider-reported model tokens. Subtract cached input from that total for a separate uncached-input-plus-output metric. Neither total represents actual currency billing. Trial runs exclude benchmark design, evaluation, the shared rendering pipeline, and the excluded setup attempts.

The initial comparison allowed 300 seconds per attempt. Grounded Animation 1 timed out without a completed-turn usage record or scene. A fresh Grounded Animation run used the same prompt and asset hashes with a 480-second cap, while other trials were finishing. The failed attempt is visible in the results. The token median uses the two completed runs.

An early renderer pass cleared Blender's default World along with the startup scene. That conflicted with the brief's factory-startup state and caused Grounded Animation 2 to fail before rendering. The final renderer uses the normal factory scene, and all published renders were made with it. Candidate Python was left as submitted.

## Shared asset

The optional input combines the release mannequin and `Idle_relaxed` GLB from KinemIQ's CC0 v1.0 archive. The original ZIP's SHA-256 is `64ca5ab4a92c9da079c5e88ca509391b0a58a24ccf2a1307b16e2f0fc6b23ffc`. The motion channels were attached to same-named nodes on the mannequin. A headless Blender import verified one skinned armature and both named actions. The shared asset is supplied for reproducibility, and any treatment could use it. [Upstream release](https://github.com/Kinemiq/free-game-animations/releases/tag/v1.0)

The project included short pointers to observations of real river flow and an existing fluid setup. It did not prescribe a water solver, camera placement, rendering style, or character implementation. The benchmark tests reuse in this small Blender task with an available local model and motion. Internet asset discovery and high-fidelity fluid coupling would need a different brief.
