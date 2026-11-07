Implemented through exactly one coding subagent; independently tested and reviewed the final diff.

- JSONL and G2 codebooks reject duplicate decoded keys at any nesting level.
- Diagnostics identify the key and, for JSONL, the one-based line.
- Five regression tests cover publication safety, file preservation, Unicode/literals, and valid repeated values.
- Passed: 27 game tests, 11 benchmark tests, and `git diff --check`.

Only the two requested files changed. No known limitations.
