from __future__ import annotations

import argparse

from common import dump_text, load_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a portfolio markdown entry from the launch manifest.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Markdown output path.")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    extension = manifest["extension"]
    repo_url = manifest["repo_url"]

    markdown = f"""# {manifest['portfolio']['title']}

> Privacy-first Chrome extension and OpenClaw publishing agent for local AI summaries.

## Summary
This project pairs a user-facing Chrome extension with an operator-facing release agent. `LocalLens` summarizes, simplifies, translates, and safe-shares page text locally with Chrome built-in AI. `OpenClaw CWS Publisher` inventories local extension repos, generates store assets, scans for leak risks, builds the extension ZIP, and drives Chrome Web Store submission through OpenClaw browser automation.

## Project Link
{manifest['portfolio']['project_link']}

## Key Features
- Local-first page and selection summaries with Chrome built-in AI
- Safe-share mode that redacts obvious sensitive strings before local AI processing
- OpenClaw publish agent for Chrome Web Store packaging, dashboard automation, and release metadata generation
- Leak-scan workflow before GitHub, ClawHub, and Chrome Web Store release

## Tech Stack
- Chrome Extension (Manifest V3)
- JavaScript
- Python
- OpenClaw
- ClawHub
- GitHub CLI

## Benchmarks & Analytics
- Extension version: {extension['version']}
- Chrome minimum version: {extension['chrome_min_version']}
- Runtime surfaces: 4 (extension, GitHub, ClawHub, portfolio)
- Privacy posture: local-only text processing

## Links
- [View on GitHub]({repo_url})
- [Open on ClawHub](https://clawhub.ai/zack-dev-cm/{manifest['clawhub']['slug']})
"""
    dump_text(args.out, markdown)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
