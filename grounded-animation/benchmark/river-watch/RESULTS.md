# Results

Sixteen completed Blender animations across eight conditions, with one timeout retained. Every published clip is four seconds at 640×360, 12 fps, and 48 frames. All used the same brief, optional inputs, model, and final renderer. [Task](task.md) · [Method and limitations](research-notes.md)

[Four-way comparison video](comparison.mp4) · [All 16 outputs at the midpoint](contact-sheet.jpg) · [Blind sampled-frame review](visual-review.md)

## Tokens by condition

Totals include cached input and reasoning output. Each median uses two completed runs and is rounded to the nearest token. The sixteen completed turns reported 6,344,682 tokens in total. The timed-out attempt produced no completed-turn usage record.

| Condition | Median total | vs. raw | Median uncached input + output | Median output | Renders |
| --- | ---: | ---: | ---: | ---: | ---: |
| raw | 182,548 | +0.0% | 21,140 | 5,416 | 2/2 |
| physics-only | 346,050 | +89.6% | 40,578 | 6,846 | 2/2 |
| reuse-only | 528,976 | +189.8% | 57,040 | 6,944 | 2/2 |
| grounded | 805,914 | +341.5% | 74,842 | 9,374 | 2/3 |
| lazy-architect | 393,872 | +115.8% | 51,536 | 6,962 | 2/2 |
| ponytail | 238,419 | +30.6% | 37,587 | 5,479 | 2/2 |
| caveman | 162,135 | -11.2% | 30,103 | 5,078 | 2/2 |
| all | 514,426 | +181.8% | 65,530 | 8,075 | 2/2 |

## What changed on screen

- Both raw outputs built their own stylized figure. Both Grounded Animation outputs and both all-skills outputs imported the shared skinned human and referenced its relaxed idle clip. The asset decision was consistent in those groups. [Raw source](results/raw-01.py) · [Grounded source](results/grounded-02.py) · [All-skills source](results/all-01.py)
- Raw scored 14/16 and 15/16 in the sampled-frame review. All skills scored 15/16 twice. The two Grounded Animation completions scored 15/16 and 16/16. The blind review showed comparable visual quality on this brief, with some stronger individual results. Scores came from one reviewer per clip and six frames per review. [Visual review](visual-review.md)
- All skills used 2.82× the raw median total. Standalone Grounded Animation used 4.41×. In both all-skills runs there were ten or eleven completed tool items, compared with five in each raw run. Caveman used 11.2% fewer total tokens, while its median uncached input plus output was higher. [Run records and source](results/)
- The person stayed on the bank. The submitted scripts used authored flow, surface detail, and moving tracers. The scene tests visible flow direction and staging, with no fluid coupling between the river and the person.

## Every attempt

| Run | Input | Cached input | Output | Reasoning output | Total | Video |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| raw-01 | 156,291 | 135,680 | 5,565 | 445 | 161,856 | [MP4](results/raw-01.mp4) |
| raw-02 | 197,973 | 187,136 | 5,268 | 195 | 203,241 | [MP4](results/raw-02.mp4) |
| physics-only-01 | 335,894 | 314,624 | 6,275 | 489 | 342,169 | [MP4](results/physics-only-01.mp4) |
| physics-only-02 | 342,512 | 296,320 | 7,418 | 417 | 349,930 | [MP4](results/physics-only-02.mp4) |
| reuse-only-01 | 595,219 | 549,376 | 7,118 | 508 | 602,337 | [MP4](results/reuse-only-01.mp4) |
| reuse-only-02 | 448,844 | 394,496 | 6,771 | 760 | 455,615 | [MP4](results/reuse-only-02.mp4) |
| grounded-01 | — | — | — | — | — | timeout, No passing render |
| grounded-02 | 998,402 | 929,408 | 9,964 | 1,310 | 1,008,366 | [MP4](results/grounded-02.mp4) |
| grounded-03 | 594,678 | 532,736 | 8,785 | 845 | 603,463 | [MP4](results/grounded-03.mp4) |
| lazy-architect-01 | 296,197 | 257,152 | 6,147 | 673 | 302,344 | [MP4](results/lazy-architect-01.mp4) |
| lazy-architect-02 | 477,624 | 427,520 | 7,776 | 1,104 | 485,400 | [MP4](results/lazy-architect-02.mp4) |
| ponytail-01 | 239,524 | 194,432 | 5,952 | 427 | 245,476 | [MP4](results/ponytail-01.mp4) |
| ponytail-02 | 226,356 | 207,232 | 5,006 | 419 | 231,362 | [MP4](results/ponytail-02.mp4) |
| caveman-01 | 125,110 | 102,912 | 4,865 | 146 | 129,975 | [MP4](results/caveman-01.mp4) |
| caveman-02 | 189,003 | 161,152 | 5,292 | 297 | 194,295 | [MP4](results/caveman-02.mp4) |
| all-01 | 550,077 | 481,664 | 8,399 | 1,222 | 558,476 | [MP4](results/all-01.mp4) |
| all-02 | 462,626 | 416,128 | 7,751 | 693 | 470,377 | [MP4](results/all-02.mp4) |
