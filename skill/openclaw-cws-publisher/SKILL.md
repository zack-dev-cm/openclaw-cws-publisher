---
name: openclaw-cws-publisher
description: Package a Chrome extension, scan tracked files for public-surface leaks, and render GitHub or ClawHub release metadata with explicit tags.
homepage: https://github.com/zack-dev-cm/openclaw-cws-publisher
license: MIT
user-invocable: true
metadata: {"openclaw":{"homepage":"https://github.com/zack-dev-cm/openclaw-cws-publisher","skillKey":"openclaw-cws-publisher","requires":{"anyBins":["python3","git","gh","clawhub"]}}}
---

# OpenClaw CWS Publisher

## Goal

Prepare a Chrome extension repo for release with less metadata drift:

- package the extension
- scan tracked files for obvious leak risks
- generate GitHub metadata
- generate optional ClawHub metadata and explicit tags
- render reproducible publish commands

## Use This Skill When

- the user wants a Chrome extension repo prepared for GitHub release
- the user wants ClawHub tags and GitHub topics kept in sync
- the user wants a leakage check before public release
- the user already has a specific repo path to release

## Operating Order

1. Build the extension ZIP.
   - `python3 {baseDir}/scripts/build_extension_zip.py --extension-dir <repo>/extension --out <zip>`
2. Scan tracked files for obvious publish leaks.
   - `python3 {baseDir}/scripts/scan_publish_surface.py --root <repo> --json-out <json> --markdown-out <md>`
3. Generate launch metadata.
   - `python3 {baseDir}/scripts/generate_launch_manifest.py --repo-root <repo> --owner <github-owner> --out <json>`
4. Render publish commands.
   - `python3 {baseDir}/scripts/render_publish_commands.py --manifest <json> --out <md>`

## Rules

- Operate on the repo path the user named, not on arbitrary sibling directories.
- Do not publish when the leak scan has unresolved findings.
- Keep GitHub topics and ClawHub tags explicit in the generated manifest.
- Do not assume generated artifacts should be committed.

## Bundled Scripts

- `scripts/build_extension_zip.py`
- `scripts/scan_publish_surface.py`
- `scripts/generate_launch_manifest.py`
- `scripts/render_publish_commands.py`
