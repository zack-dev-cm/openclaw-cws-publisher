# AGENTS.md

This repository ships `openclaw-cws-publisher`, a public release-kit skill for
Chrome extension repos. Use this file as the index, not as the full manual.

## Operating Rules

- Restate the goal and name the verification step before editing files.
- Keep diffs surgical. Do not refactor adjacent release-kit helpers unless the task needs it.
- Treat public-surface review as part of the default loop. New docs, scripts, examples, and fixtures must clear leak and bleed checks.
- Put durable knowledge in `docs/codex/`. Keep this file short.
- Use `.codex/agents/` only when the user explicitly asks for delegation or parallel agent work.

## Scope

This repo is the public release kit for Chrome extension repos. It is not the place to ship a specific extension product, store screenshots, or browser-profile automation.

## Repo Map

- [Overview](docs/codex/overview.md)
- [Architecture](docs/codex/architecture.md)
- [Workflow](docs/codex/workflow.md)
- [Evals](docs/codex/evals.md)
- [Cleanup](docs/codex/cleanup.md)

## Deployment Rules

When preparing a release from this repo:

1. Keep product assets in the target extension repo.
2. Run the leak scan against tracked files before generating publish commands.
3. Set GitHub description, homepage, and topics explicitly. Do not leave repo metadata blank.
4. Set ClawHub tags explicitly on every publish. Do not rely on inherited `latest` only.
5. Keep GitHub topics and ClawHub tags aligned in the generated manifest.
6. Do not commit generated `dist/` outputs or audit reports unless the user explicitly wants checked-in examples.
7. Do not add arbitrary filesystem inventory or logged-in browser automation to the public skill surface.
8. If a target repo has a reviewer gate, render it as a preflight step before any GitHub or ClawHub publish command.
9. If a Chrome Web Store draft is already pending review, do not recommend cancel/resubmit unless a verified acceptance blocker exists.
10. Validate the exact ZIP intended for CWS upload against source manifest and listing JSON before calling a release ready.
11. Block stale ZIPs, unjustified host permissions, Manifest V2, `tabs`, `debugger`, `<all_urls>`, remote-code patterns, and listing/privacy drift.
12. Require a design/UI/UX gate with scores of at least `8/10` for product clarity, visual trust, evidence integrity, responsive polish, accessibility, and claim alignment.
13. Record current Chrome Stable release data before relying on local E2E as current-browser evidence.
14. Run or record a competitor/differentiation check before first public CWS launch.

## Required Metadata

- GitHub description
- GitHub homepage
- GitHub topics
- ClawHub slug
- ClawHub name
- ClawHub tags

## Separation Rules

- Extension product repos stay separate from this release-kit repo.
- Browser automation for Chrome Web Store dashboards is operator-only and must not be bundled into the public ClawHub skill.

## Default Verification

1. Run `python3 -m py_compile skill/openclaw-cws-publisher/scripts/*.py`.
2. Run `python3 -m pytest -q`.
3. Run `python3 -m codex_harness audit . --strict --min-score 90` when the harness package is available.
4. Review changed public files for secrets, private paths, private URLs, customer data, and evidence drift.

## Project-Scoped Custom Agents

- `.codex/agents/architect.toml`
- `.codex/agents/implementer.toml`
- `.codex/agents/reviewer.toml`
- `.codex/agents/evolver.toml`
- `.codex/agents/cleanup.toml`
