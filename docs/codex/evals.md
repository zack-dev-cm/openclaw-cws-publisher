# Evals

## Required Checks

- Compile: `python3 -m py_compile skill/openclaw-cws-publisher/scripts/*.py`
- Unit tests: `python3 -m pytest -q`
- Release gate: `python3 -m codex_harness audit . --strict --min-score 90`

## Release-Blocking Behaviors

- A leak finding report contains an unredacted token-like value.
- A ZIP requests unjustified host permissions, Manifest V2, remote code, `tabs`, `debugger`, or `<all_urls>`.
- Listing copy, privacy text, or reviewer instructions disagree with the shipped manifest.
- Generated publish commands omit explicit GitHub topics or ClawHub tags.

## Regression Fixtures

Tests should use synthetic values assembled at runtime when they need token-shaped input, so the repository itself does not contain committed secret-like strings.
