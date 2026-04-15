# OpenClaw CWS Publisher

Open-source OpenClaw agent for shipping Chrome extensions with less manual drift.

This repo contains two deliverables:

- `extension/`: `LocalLens: Private AI Summaries`, a Chrome extension that summarizes, simplifies, translates, and safe-shares page text locally with Chrome built-in AI.
- `skill/openclaw-cws-publisher/`: a ClawHub-ready OpenClaw skill that inventories local extension repos, builds a ZIP, generates store copy, scans for leak risks, and drives Chrome Web Store publication through `openclaw browser`.

## Why This Product

The extension idea is intentionally narrow and policy-friendly:

- current Chrome AI momentum is real, but generic all-in-one AI sidebars are crowded
- Chrome now exposes built-in AI APIs for summarization and prompting on stable channels
- Chrome Web Store review strongly prefers a single purpose, minimal permissions, and clear privacy disclosures
- this machine already has multiple AI chat and devtools extensions, so the new item avoids that overlap

The result is a privacy-first utility with a broader audience than a developer-only tool and a cleaner review surface than a server-backed copilot.

## Repo Layout

```text
docs/                              research and generated inventory
extension/                         LocalLens MV3 extension
marketing/                         HTML sources for store assets
skill/openclaw-cws-publisher/      publish agent skill
tests/                             smoke tests for inventory/build/audit logic
```

## Quick Start

```bash
cd openclaw-cws-publisher
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

python3 skill/openclaw-cws-publisher/scripts/generate_marketing_assets.py \
  --repo-root .

python3 skill/openclaw-cws-publisher/scripts/build_extension_zip.py \
  --extension-dir extension \
  --out dist/locallens-extension.zip

python3 skill/openclaw-cws-publisher/scripts/inventory_local_extensions.py \
  --search-root ~/Documents/GitHub \
  --markdown-out docs/local_extension_inventory.md \
  --json-out dist/local_extension_inventory.json

python3 skill/openclaw-cws-publisher/scripts/run_agent.py \
  --repo-root . \
  --search-root ~/Documents/GitHub \
  --browser-profile openclaw-cws-publisher
```

## Publish Flow

1. Inventory local extension repos so you do not clone an already-shipped idea.
2. Generate the Chrome extension ZIP and store assets.
3. Scan the repo for obvious publish leaks.
4. Generate store listing copy and release metadata.
5. Launch Chrome Web Store dashboard automation through OpenClaw.
6. Publish the skill to ClawHub and add the portfolio entry.

## Research

The decision memo and official source links live in [docs/research.md](docs/research.md).

## Compliance Artifacts

- Privacy policy: [docs/privacy-policy.md](docs/privacy-policy.md)
- Reviewer test instructions: [docs/test-instructions.md](docs/test-instructions.md)

## License

MIT
