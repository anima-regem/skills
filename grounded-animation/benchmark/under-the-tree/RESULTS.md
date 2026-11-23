# Results

Thirteen completed runs across eight conditions. Every completed scene produced a playable preview. Eight other attempts timed out. Each candidate built the same [four-second close-up](task.md) with the same optional inputs. All review clips use a common 640×360 Eevee draft render sampled at 6 fps. [Method and limitations](research-notes.md)

[Four-way comparison](comparison.mp4) · [All completed clips at the midpoint](contact-sheet.jpg) · [All-skills example at 12 fps](full-speed-all-02.mp4) · [Blind sampled-frame review](visual-review.md)

[Directed 1280×720 close-up](hero.png) · [Blender still source](hero.py). The directed image is separate from the measured trials.

## Tokens by condition

The 13 completed turns reported 20,438,645 tokens, including cached input and reasoning output. The timed-out turns lack completed-turn usage. The median is rounded to the nearest token. Here the render count also gives the count of completed turns over attempts.

| Condition | Median total | vs. raw | Median uncached input + output | Median output | Renders |
| --- | ---: | ---: | ---: | ---: | ---: |
| raw | 877,198 | +0.0% | 51,086 | 8,593 | 2/2 |
| physics-only | 1,390,531 | +58.5% | 71,107 | 11,953 | 1/3 |
| reuse-only | 2,452,588 | +179.6% | 114,220 | 13,300 | 2/3 |
| grounded | 1,494,851 | +70.4% | 52,291 | 10,825 | 1/3 |
| lazy-architect | 1,251,314 | +42.6% | 65,650 | 10,208 | 2/3 |
| ponytail | 1,776,026 | +102.5% | 100,314 | 10,276 | 2/2 |
| caveman | 1,400,786 | +59.7% | 90,386 | 11,170 | 2/2 |
| all | 2,037,441 | +132.3% | 99,777 | 11,788 | 1/3 |

## What changed on screen

- Both raw runs and all completed guided runs used the supplied face rig. A close-up brief and a suitable optional model made reuse the baseline behavior. In the river benchmark the raw runs built their own figures. [Raw close-up source](results/raw-01.py) · [River comparison](../river-watch/RESULTS.md)
- The raw clips scored 12/16 and 13/16 in the blind frame review. The completed all-skills clip scored 12/16. Eye shifts, squints, and reopening were easier to see than mouth changes under the moustache. Passing leaves carried the clearest wind cue. The blurred field made plant motion harder to judge. [Visual review](visual-review.md)
- The completed all-skills run used 2.32× the raw median total and made 31 completed tool calls. The two raw runs made 17 and 22. Full Grounded Animation and all skills each timed out twice, so each median represents one completed turn. Several candidates repeatedly probed rendering or scene construction. The result includes that work and depends on the test environment. [Run records](results/)

## Every attempt

| Run | Input | Cached input | Output | Reasoning output | Total | Video |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| raw-01 | 823,912 | 775,552 | 7,378 | 690 | 831,290 | [MP4](results/raw-01.mp4) |
| raw-02 | 913,297 | 876,672 | 9,808 | 1,936 | 923,105 | [MP4](results/raw-02.mp4) |
| physics-only-01 | — | — | — | — | — | timeout, No passing render |
| physics-only-02 | — | — | — | — | — | timeout, No passing render |
| physics-only-03 | 1,378,578 | 1,319,424 | 11,953 | 1,943 | 1,390,531 | [MP4](results/physics-only-03.mp4) |
| reuse-only-01 | 1,589,368 | 1,507,328 | 10,717 | 1,600 | 1,600,085 | [MP4](results/reuse-only-01.mp4) |
| reuse-only-02 | — | — | — | — | — | timeout, No passing render |
| reuse-only-03 | 3,289,207 | 3,169,408 | 15,884 | 4,870 | 3,305,091 | [MP4](results/reuse-only-03.mp4) |
| grounded-01 | — | — | — | — | — | timeout, No passing render |
| grounded-02 | 1,484,026 | 1,442,560 | 10,825 | 2,253 | 1,494,851 | [MP4](results/grounded-02.mp4) |
| grounded-03 | — | — | — | — | — | timeout, No passing render |
| lazy-architect-01 | 816,178 | 748,032 | 8,131 | 821 | 824,309 | [MP4](results/lazy-architect-01.mp4) |
| lazy-architect-02 | — | — | — | — | — | timeout, No passing render |
| lazy-architect-03 | 1,666,036 | 1,623,296 | 12,284 | 2,346 | 1,678,320 | [MP4](results/lazy-architect-03.mp4) |
| ponytail-01 | 2,000,702 | 1,900,544 | 10,112 | 2,204 | 2,010,814 | [MP4](results/ponytail-01.mp4) |
| ponytail-02 | 1,530,798 | 1,450,880 | 10,439 | 1,873 | 1,541,237 | [MP4](results/ponytail-02.mp4) |
| caveman-01 | 1,474,992 | 1,424,640 | 12,021 | 2,450 | 1,487,013 | [MP4](results/caveman-01.mp4) |
| caveman-02 | 1,304,238 | 1,196,160 | 10,320 | 1,634 | 1,314,558 | [MP4](results/caveman-02.mp4) |
| all-01 | — | — | — | — | — | timeout, No passing render |
| all-02 | 2,025,653 | 1,937,664 | 11,788 | 2,669 | 2,037,441 | [MP4](results/all-02.mp4) |
| all-03 | — | — | — | — | — | timeout, No passing render |
