from __future__ import annotations

import argparse
from pathlib import Path

from common import abs_path, dump_json, load_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Chrome Web Store listing copy and metadata.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    launch_manifest = load_json(args.manifest)

    payload = {
        "name": launch_manifest["extension"]["name"],
        "short_description": "Private page summaries, rewrites, translations, and safe-share cleanup powered by Chrome built-in AI.",
        "detailed_description": (
            "LocalLens helps you move through dense pages faster without routing tab text to an external server.\n\n"
            "What it does:\n"
            "- Summarizes the current page into useful key points\n"
            "- Summarizes selected text for fast scanning\n"
            "- Simplifies dense writing into plainer language\n"
            "- Translates selected text inside the popup\n"
            "- Creates safe-share briefs by masking obvious sensitive strings before local AI processing\n\n"
            "Why people use it:\n"
            "- No account or API key\n"
            "- Active-tab only workflow\n"
            "- Minimal permissions\n"
            "- Built for privacy-sensitive reading and collaboration workflows\n\n"
            "Technical note:\n"
            "LocalLens targets Chrome 138+ with built-in AI support. If your browser has not downloaded the local model yet, Chrome may need a short warm-up download on first use."
        ),
        "category": "Productivity",
        "single_purpose": (
            "Summarize, simplify, translate, and safely rewrite text from the active tab with Chrome built-in AI while keeping the workflow local-first."
        ),
        "privacy": {
            "stores_data": "No",
            "sells_data": "No",
            "shares_data": "No",
            "uses_external_servers": "No",
            "justification": (
                "LocalLens reads text from the active tab only after the user clicks an action. The extension uses Chrome built-in AI locally and does not send captured text to a remote API."
            ),
        },
        "store_assets": {
            "icon": str(repo_root / "extension" / "icons" / "icon128.png"),
            "screenshot_1": str(repo_root / "dist" / "store-assets" / "locallens-store-screenshot-1.png"),
            "promo_small": str(repo_root / "dist" / "store-assets" / "locallens-promo-small.png"),
        },
        "keywords": [
            "ai summary",
            "private summary",
            "local ai",
            "page summary",
            "translate text",
            "safe share",
            "chrome built-in ai",
        ],
    }
    dump_json(args.out, payload)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
