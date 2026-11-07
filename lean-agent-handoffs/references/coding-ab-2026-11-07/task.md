Implement a real parser bug fix in this checkout using exactly one coding subagent. As coordinator, delegate the edits, independently run the tests and inspect the final diff, and relay any required corrections to that same worker. Do not create extra agents or implement the fix yourself.

Game JSON input currently accepts duplicate JSON object keys with last-value-wins behavior. Fix duplicate-key rejection for JSONL game input and G2 codebook loading. Detect decoded-equivalent names such as id and \u0069d, and duplicates in any JSON object. For JSONL, report the one-based line and duplicated key. Codebook diagnostics must identify the duplicated key. A late invalid record must fail before reviewer-file publication or spectator output. Preserve existing files, existing syntax-error handling, Unicode/U+2028 and quoted literals, valid repeated values across separate records, and valid G1/G2 behavior.

Only edit compact-agent-handoffs/scripts/game.py and compact-agent-handoffs/scripts/test_game.py. Add focused regression tests. Do not modify benchmark files, agent instructions, global configuration, or files outside this checkout. Do not commit, push, use the network, or read sibling checkouts or the observer's acceptance harness. The coding worker must not delegate further.

Use this preinstalled interpreter, with dependencies already cached:
$RUN_DIR/runtime/bin/python

Run at least:
$RUN_DIR/runtime/bin/python -B -m unittest discover -s compact-agent-handoffs/scripts -p test_game.py -v
$RUN_DIR/runtime/bin/python -B -m unittest discover -s lean-agent-handoffs/scripts -p test_benchmark.py -v

Return a concise summary of the change, test counts, and any limitations.

Test environment detail shared by both measured arms: temporary test fixtures may live inside the checkout. The tokenizer cache is separate and already contains both vocabularies at $RUN_DIR/tokenizer-cache. Preserve or explicitly set TIKTOKEN_CACHE_DIR to that directory when running the interpreter, even if TMPDIR changes. No vocabulary downloads are needed.
