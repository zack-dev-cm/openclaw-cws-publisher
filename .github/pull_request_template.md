## Summary

-

## Verification

- [ ] `python3 -m py_compile skill/openclaw-cws-publisher/scripts/*.py`
- [ ] `python3 -m pytest -q`
- [ ] `python3 -m codex_harness audit . --strict --min-score 90`

## Security And Public-Surface Review

- [ ] No secrets, token-shaped strings, private paths, local endpoints, dashboard dumps, or customer identifiers.
- [ ] Security, leak, and public-surface review is complete for changed docs, scripts, fixtures, and generated examples.
- [ ] Generated reports are redacted or intentionally untracked.
- [ ] GitHub topics and ClawHub tags stay explicit when publish behavior changes.
