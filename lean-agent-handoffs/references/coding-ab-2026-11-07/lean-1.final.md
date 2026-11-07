Implemented by exactly one coding subagent; I independently reviewed the final diff and ran both suites.

Duplicate decoded keys, including nested objects and escaped names, now fail with key diagnostics and one-based JSONL line numbers. Regressions verify publication safety, file preservation, syntax errors, Unicode/literals, and valid G1/G2 behavior.

- Game tests: **29 passed**
- Benchmark tests: **11 passed**
- `git diff --check`: passed

Only the two authorized files changed. No known limitations within the requested scope.
