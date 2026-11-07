Implemented through exactly one coding worker; I independently reviewed the diff and ran both required suites.

- Rejects duplicate keys at every object depth, including `id` / `\u0069d`.
- JSONL errors identify the line and key; codebook errors identify the key.
- Added 7 regression tests covering publication safety and preserved G1/G2 behavior.
- Passed: **29 game tests + 11 benchmark tests**. Diff check passed; only the two authorized files changed.

The initial worker test run attempted unavailable tokenizer downloads after a cache-path change. Final verification used the existing cached assets and passed.
