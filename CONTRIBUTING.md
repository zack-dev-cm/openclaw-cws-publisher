# Contributing

This repo is a public release kit for Chrome extension repos. Contributions
should improve the skill surface, helper scripts, tests, or release docs without
adding product-specific assets or dashboard automation.

## Local Checks

```bash
python3 -m py_compile skill/openclaw-cws-publisher/scripts/*.py
python3 -m pytest -q
python3 -m codex_harness audit . --strict --min-score 90
```

## Public-Surface Rules

- Do not commit secrets, token-shaped strings, private paths, local endpoints, dashboard dumps, or customer identifiers.
- Keep generated `dist/` outputs out of source control unless they are explicitly reviewed examples.
- Add tests for changed helper behavior.
- Keep Chrome Web Store dashboard actions operator-only and outside the public skill bundle.
