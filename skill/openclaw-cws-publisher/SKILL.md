---
name: openclaw-cws-publisher
description: Build, package, audit, and publish a Chrome extension with OpenClaw browser automation, GitHub release artifacts, ClawHub metadata, and portfolio-ready copy.
homepage: https://github.com/zack-dev-cm/openclaw-cws-publisher
license: MIT
user-invocable: true
metadata: {"openclaw":{"homepage":"https://github.com/zack-dev-cm/openclaw-cws-publisher","skillKey":"openclaw-cws-publisher","requires":{"anyBins":["python3","git","gh","clawhub","openclaw","sips"]}}}
---

# OpenClaw CWS Publisher

## Goal

Ship a Chrome extension with less manual release drift:

- scan local extension repos
- package the extension
- generate screenshots and promo art
- scan for obvious leak risks
- generate store, GitHub, ClawHub, and portfolio metadata
- drive Chrome Web Store submission with `openclaw browser`

## Use This Skill When

- the user wants a new Chrome extension prepared for launch
- the user wants an OpenClaw-based publish agent for Chrome Web Store work
- the user wants GitHub, ClawHub, and portfolio release artifacts kept in one repo
- the user wants a leakage check before public release

## Operating Order

1. Generate marketing assets.
   - `python3 {baseDir}/scripts/generate_marketing_assets.py --repo-root <repo>`
2. Inventory local extension repos.
   - `python3 {baseDir}/scripts/inventory_local_extensions.py --search-root <root> --markdown-out <md> --json-out <json>`
3. Build the extension ZIP.
   - `python3 {baseDir}/scripts/build_extension_zip.py --extension-dir <repo>/extension --out <zip>`
4. Scan the repo for obvious publish leaks.
   - `python3 {baseDir}/scripts/scan_publish_surface.py --root <repo> --json-out <json> --markdown-out <md>`
5. Generate launch metadata.
   - `python3 {baseDir}/scripts/generate_launch_manifest.py --repo-root <repo> --out <json>`
   - `python3 {baseDir}/scripts/generate_listing_copy.py --repo-root <repo> --manifest <json> --out <json>`
   - `python3 {baseDir}/scripts/render_portfolio_entry.py --manifest <json> --out <md>`
   - `python3 {baseDir}/scripts/render_publish_commands.py --manifest <json> --out <md>`
6. Publish through OpenClaw when credentials are present.
   - `python3 {baseDir}/scripts/publish_extension.py --repo-root <repo> --manifest <json> --listing <json> --zip-path <zip> --browser-profile <profile>`

## Rules

- Prefer a single-purpose extension with minimal permissions.
- Do not publish when the leak scan has unresolved findings.
- Do not assume Chrome Web Store login is active; detect it from the dashboard snapshot.
- Keep GitHub, ClawHub, and portfolio copy aligned with one manifest.
- If browser automation cannot safely locate a publishing control, stop and save the latest dashboard snapshot instead of guessing.

## Bundled Scripts

- `scripts/generate_marketing_assets.py`
- `scripts/inventory_local_extensions.py`
- `scripts/build_extension_zip.py`
- `scripts/scan_publish_surface.py`
- `scripts/generate_launch_manifest.py`
- `scripts/generate_listing_copy.py`
- `scripts/render_release_notes.py`
- `scripts/render_portfolio_entry.py`
- `scripts/render_publish_commands.py`
- `scripts/publish_extension.py`
- `scripts/run_agent.py`
