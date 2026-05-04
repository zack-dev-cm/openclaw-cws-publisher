# Overview

`openclaw-cws-publisher` is a public release kit for Chrome extension repos.
It packages a target extension, checks the exact Web Store ZIP and listing
contract, scans public files for leak risks, and renders GitHub plus ClawHub
publish commands.

## Product

- Primary user: an operator preparing a Chrome extension repo for public release.
- Core job: make release readiness explicit before a GitHub or ClawHub publish step.
- Non-goal: operating the Chrome Web Store dashboard or storing product-specific assets.

## Repo Landmarks

- Skill surface: `skill/openclaw-cws-publisher/SKILL.md`
- Helper scripts: `skill/openclaw-cws-publisher/scripts/`
- Regression tests: `tests/test_release_kit.py`
- Release guidance: `README.md`, `AGENTS.md`, and this `docs/codex/` map.

## Standard Checks

- Compile: `python3 -m py_compile skill/openclaw-cws-publisher/scripts/*.py`
- Tests: `python3 -m pytest -q`
- Open-source gate: `python3 -m codex_harness audit . --strict --min-score 90`
