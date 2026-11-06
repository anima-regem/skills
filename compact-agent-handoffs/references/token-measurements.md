# Token measurements

The paired handoffs cover delegation, progress, partial work, a blocker, a clarification, an exact error, completion, and a minimal update. The same facts are present in both sets. Each blank line separates two messages.

With `o200k_base`, the eight messages went from 163 to 130 tokens, a 20.2% reduction. A single 286-token read of `SKILL.md` is offset after about 70 handoffs at that average saving. Tool envelopes, prompt caching, and messages skipped by following the skill are outside this estimate.

## Concise English

```text
Audit only src/auth.ts for redirect loops. Report file and line numbers for any findings. Do not edit files.

I reproduced the bug on Safari 18. Chrome 131 did not reproduce it. I’ll check the redirect branch next.

I finished the parser review and found no issues. The worker review is pending because fixtures are missing.

The staging test is blocked by HTTP 401. Please send the name of the staging credential so I can retry.

Should an empty array mean no results or an invalid request? This determines the response code.

The error at src/cache.ts:89 is exactly "miss | busy; retry". It happens after two failed retries.

I added the missing return in src/auth.ts:74. All 12 auth tests passed. I did not run the full suite.

Already merged.
```

## Compact handoffs

```text
Task: Audit src/auth.ts only for redirect loops. Read only. Report findings with file:line.

Safari 18: reproduced. Chrome 131: no repro. Next: check redirect branch.

Parser reviewed, no issues. Worker review pending missing fixtures.

Blocked: staging test, HTTP 401. Need staging credential name to retry.

Ask: Empty array means no results or invalid request? Determines response code.

src/cache.ts:89 error "miss | busy; retry" after 2 failed retries.

Done: Added missing return at src/auth.ts:74. Auth tests: 12 passed. Full suite: not run.

Already merged.
```

## Reproduce

Run from the repository root. The tokenizer measures each message separately, then estimates how many handoffs cover one full read of `SKILL.md` at the observed average saving.

```bash
uv run --isolated --with tiktoken==0.12.0 python - <<'PY'
import re
from pathlib import Path

import tiktoken

skill = Path("compact-agent-handoffs")
fixture = (skill / "references/token-measurements.md").read_text(encoding="utf-8")
encoding = tiktoken.get_encoding("o200k_base")
baseline, compact = [
    [len(encoding.encode_ordinary(message)) for message in block.split("\n\n")]
    for block in re.findall(r"^```text\n(.+?)\n```$", fixture, flags=re.M | re.S)
]
assert len(baseline) == len(compact) == 8
before, after = sum(baseline), sum(compact)
setup = len(encoding.encode_ordinary((skill / "SKILL.md").read_text(encoding="utf-8")))
saved = before - after
print(f"Per message: {list(zip(baseline, compact))}")
print(f"Payload: {before} → {after} tokens ({saved / before:.1%} fewer)")
print(f"One full read: {setup} tokens")
if saved > 0:
    print(f"Net savings after one read: {setup * len(baseline) // saved + 1} handoffs")
PY
```
