from __future__ import annotations

import argparse

from common import dump_text, load_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Render concise GitHub release notes from the launch manifest.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Markdown output path.")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    extension = manifest["extension"]

    text = f"""# {manifest['release']['title']}

## What shipped

- `LocalLens` Chrome extension v{extension['version']}
- OpenClaw publish skill for Chrome Web Store packaging and dashboard automation
- Local extension inventory report for your GitHub workspace
- Store assets, privacy copy, portfolio copy, and publish command sheet

## Product position

LocalLens is a privacy-first Chrome extension that summarizes, simplifies, translates, and safe-shares active-tab text with Chrome built-in AI.

## Notes

- No external inference server required
- Minimal extension permissions
- Release includes leak-scan and packaging helpers for repeatable future updates
- ClawHub package now ships with an explicit MIT license file in the published skill folder
"""
    dump_text(args.out, text)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
