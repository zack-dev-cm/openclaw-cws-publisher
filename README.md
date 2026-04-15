# OpenClaw CWS Publisher

Repo-local release helpers for Chrome extension projects.

This repo now ships one public deliverable:

- `skill/openclaw-cws-publisher/`: a ClawHub-ready release kit for packaging an extension, scanning tracked files for public-surface leaks, generating GitHub metadata, and rendering publish commands with explicit GitHub topics and ClawHub tags.

The LocalLens extension was split out of this repo. Product assets, Chrome Web Store copy, and extension-specific docs no longer belong in the public publisher package.

## What This Repo Does

- zip a target `extension/` directory for Chrome Web Store upload
- scan tracked files for absolute paths, localhost URLs, websocket URLs, and token-shaped strings
- derive GitHub and optional ClawHub release metadata from a target extension manifest
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

python3 skill/openclaw-cws-publisher/scripts/scan_publish_surface.py \
  --root /path/to/extension-repo \
  --json-out /path/to/extension-repo/dist/publish-surface.json \
  --markdown-out /path/to/extension-repo/docs/publish-surface.md

python3 skill/openclaw-cws-publisher/scripts/generate_launch_manifest.py \
  --repo-root /path/to/extension-repo \
  --owner your-github-owner \
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
- `docs/privacy-policy.md`
- `docs/test-instructions.md`

Optional:

- a ClawHub skill slug and name if the target repo also publishes a public skill
- extra GitHub topics and ClawHub tags through the manifest generator flags

## Security Posture

- the leak scan now operates on tracked files from `git ls-files`
- generated artifacts are not meant to be committed by default
- browser automation is intentionally kept out of the public skill surface

## License

MIT
