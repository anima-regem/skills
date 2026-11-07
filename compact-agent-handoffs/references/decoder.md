# Decode H1 messages

H1 is a public, fixed vocabulary for handoff fields. The sender and recipient select it through the shared skill. A message contains one or more lines with a code, an ASCII space, and text. Every field carries its ordinary meaning.

| Code | Expanded field |
| --- | --- |
| T | Task |
| U | Update |
| D | Done |
| B | Blocked |
| Q | Ask |
| S | Scope |
| C | Check |
| N | Next |

`S ro` expands to `Scope: Read only.` This is the sole content macro. All other text remains literal, including punctuation, quoted errors, whitespace inside fields, and Unicode. Field order and repeated fields are preserved. A pending task can use `U` with its pending status stated explicitly.

Run the decoder from the repository root with Python 3.9 or later. It uses the standard library.

```bash
python3 compact-agent-handoffs/scripts/decode.py <<'H1'
D src/auth.ts:74 added missing return
C auth tests 12 passed; full suite not run
H1
```

The output is ready for review.

```text
Done: src/auth.ts:74 added missing return
Check: auth tests 12 passed; full suite not run
```

Pass a UTF-8 file path in place of stdin when reviewing a saved message. The decoder validates the entire message before writing output. Unknown codes, empty fields, and blank records produce an error with a line number. A single trailing newline is accepted. Code letters and the `ro` macro are case-sensitive.

Use the decoder on H1 messages. Ordinary prose, multiline literals, and approvals use the normal text channel. The decoder expands field meanings and the documented macro. A reviewer still checks that the sender's summary preserves the underlying facts.
