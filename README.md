# OpenClaw CWS Publisher

Repo-local release helpers for Chrome extension projects.

This repo now ships one public deliverable:

- `skill/openclaw-cws-publisher/`: a ClawHub-ready release kit for packaging an extension, validating the exact CWS ZIP/listing/privacy contract, running local E2E and design gates, checking current Chrome Stable release data, scanning competitors and leaks, generating GitHub metadata, and rendering publish commands with explicit GitHub topics and ClawHub tags.

The LocalLens extension was split out of this repo. Product assets, Chrome Web Store copy, and extension-specific docs no longer belong in the public publisher package.

## What This Repo Does

- zip a target `extension/` directory for Chrome Web Store upload
- validate the exact ZIP intended for upload against source manifest and CWS listing JSON
- scan tracked and untracked non-ignored files for absolute paths, localhost URLs, websocket URLs, and token-shaped strings while redacting matched values in reports
- run discovered local CWS reviewer/E2E gates
- enforce design, UI, screenshot, responsive, accessibility, and claim-alignment score gates
- check the Chrome for Testing last-known-good Stable release before declaring E2E coverage fresh
- run a lightweight competitor/differentiation check for risky listing claims
- derive GitHub and optional ClawHub release metadata from a target extension manifest
- detect repo-local reviewer gates and render them as preflight checks
- render reproducible `gh repo edit`, `gh release create`, and `clawhub publish --tags ...` commands

## What This Repo Does Not Do

- it does not inventory arbitrary filesystem trees by default
- it does not ship a bundled Chrome extension product
- it does not drive a logged-in browser profile as part of the public ClawHub skill

## Repo Layout

```text
skill/openclaw-cws-publisher/      public release-kit skill
tests/                             smoke tests for zip, audit, and manifest helpers
```

## Quick Start

Run these helpers from the extension repo you want to release.

```bash
cd openclaw-cws-publisher
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

python3 skill/openclaw-cws-publisher/scripts/build_extension_zip.py \
  --extension-dir /path/to/extension-repo/extension \
  --out /path/to/extension-repo/dist/extension.zip

python3 skill/openclaw-cws-publisher/scripts/validate_cws_package.py \
  --zip /path/to/extension-repo/dist/extension.zip \
  --source-manifest /path/to/extension-repo/extension/manifest.json \
  --listing-json /path/to/extension-repo/docs/cws/listing.json \
  --json-out /path/to/extension-repo/dist/cws-package-check.json \
  --markdown-out /path/to/extension-repo/docs/cws-package-check.md

python3 skill/openclaw-cws-publisher/scripts/scan_publish_surface.py \
  --root /path/to/extension-repo \
  --json-out /path/to/extension-repo/dist/publish-surface.json \
  --markdown-out /path/to/extension-repo/docs/publish-surface.md

python3 skill/openclaw-cws-publisher/scripts/run_local_e2e_gates.py \
  --repo-root /path/to/extension-repo \
  --json-out /path/to/extension-repo/dist/local-e2e-gates.json \
  --markdown-out /path/to/extension-repo/docs/local-e2e-gates.md

python3 skill/openclaw-cws-publisher/scripts/check_design_gate.py \
  --design-report /path/to/extension-repo/docs/design-gate.json \
  --json-out /path/to/extension-repo/dist/design-gate-check.json

python3 skill/openclaw-cws-publisher/scripts/check_chrome_release.py \
  --tested-chrome-version "$(google-chrome --version | awk '{print $3}')" \
  --json-out /path/to/extension-repo/dist/chrome-stable-check.json

python3 skill/openclaw-cws-publisher/scripts/check_competitors.py \
  --listing-json /path/to/extension-repo/docs/cws/listing.json \
  --competitors-json /path/to/extension-repo/docs/cws/competitors.json \
  --markdown-out /path/to/extension-repo/docs/cws-competitor-check.md

python3 skill/openclaw-cws-publisher/scripts/generate_launch_manifest.py \
  --repo-root /path/to/extension-repo \
  --owner your-github-owner \
  --public-site-base https://your-extension.pages.dev \
  --clawhub-slug your-extension-slug \
  --clawhub-name "Your Extension Skill" \
  --out /path/to/extension-repo/dist/launch-manifest.json

python3 skill/openclaw-cws-publisher/scripts/render_publish_commands.py \
  --manifest /path/to/extension-repo/dist/launch-manifest.json \
  --out /path/to/extension-repo/dist/publish-commands.md
```

## Release Contract

The target repo should provide:

- `extension/manifest.json`
- `docs/cws/listing.json`
- `docs/privacy-policy.md`
- `docs/test-instructions.md`

Optional:

- a ClawHub skill slug and name if the target repo also publishes a public skill
- a dedicated public support/privacy site, ideally on Cloudflare Workers or Cloudflare Pages; pass `--public-site-base` or export `CWS_PUBLIC_SITE_BASE`
- a repo-local reviewer gate such as `scripts/reviewer_gate.py` and `.githooks/pre-push` when the extension needs policy/runtime review before publish
- a `docs/design-gate.json` score report for public pages, extension UI, CWS media, screenshots, responsive behavior, accessibility, and claim alignment
- a `docs/cws/competitors.json` file with at least three competitor or substitute products before first public launch
- extra GitHub topics and ClawHub tags through the manifest generator flags

## Security Posture

- the leak scan now operates on tracked and untracked non-ignored files from `git ls-files`
- release readiness should be based on the ZIP intended for upload, not source-only assumptions
- persistent host permissions are blocked by default; use `activeTab` plus `scripting` after user action unless a shipped feature truly requires host access
- no-host packages must not carry host-permission justifications or stale host-access language in listing copy
- design evidence must be recorded and pass the score gate before CWS dashboard upload
- Chrome Stable freshness must be recorded so local E2E is not silently behind the current release channel
- generated artifacts are not meant to be committed by default
- browser automation is intentionally kept out of the public skill surface
- pending Chrome Web Store drafts should not be canceled for nonblocking hardening; queue those changes for the next patch version

## License

MIT
