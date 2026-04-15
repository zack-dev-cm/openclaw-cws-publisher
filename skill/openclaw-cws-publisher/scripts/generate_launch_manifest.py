from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import abs_path, dump_json, slugify


def build_launch_manifest(repo_root: Path) -> dict:
    manifest = json.loads((repo_root / "extension" / "manifest.json").read_text(encoding="utf-8"))
    repo_name = repo_root.name
    extension_name = manifest["name"]
    repo_url = f"https://github.com/zack-dev-cm/{repo_name}"
    skill_slug = "openclaw-cws-publisher"
    portfolio_slug = slugify(extension_name)
    return {
        "repo_name": repo_name,
        "repo_url": repo_url,
        "support_url": f"{repo_url}/issues",
        "privacy_policy_url": f"{repo_url}/blob/main/docs/privacy-policy.md",
        "test_instructions_url": f"{repo_url}/blob/main/docs/test-instructions.md",
        "github_topics": [
            "chrome-extension",
            "openclaw",
            "browser-automation",
            "built-in-ai",
            "privacy",
        ],
        "clawhub": {
            "slug": skill_slug,
            "name": "OpenClaw CWS Publisher",
            "version": manifest["version"],
            "description": "OpenClaw skill for packaging and publishing Chrome extensions with leak checks and browser automation.",
        },
        "extension": {
            "name": extension_name,
            "version": manifest["version"],
            "summary": manifest["description"],
            "category": "Tools",
            "chrome_min_version": manifest.get("minimum_chrome_version", ""),
        },
        "portfolio": {
            "title": "OpenClaw CWS Publisher + LocalLens",
            "slug": portfolio_slug,
            "project_link": f"https://zack-dev-cm.github.io/projects/{portfolio_slug}.md",
        },
        "release": {
            "tag": f"v{manifest['version']}",
            "title": f"Initial public release: {extension_name}",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one manifest for GitHub, ClawHub, store, and portfolio metadata.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    payload = build_launch_manifest(repo_root)
    dump_json(args.out, payload)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
