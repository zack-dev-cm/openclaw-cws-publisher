from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from common import abs_path


SCRIPT_DIR = Path(__file__).resolve().parent


def run_step(*args: str) -> None:
    command = ["python3", str(SCRIPT_DIR / args[0]), *args[1:]]
    result = subprocess.run(command, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the end-to-end extension publish preparation workflow.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--search-root", required=True, help="Filesystem root to scan for local extensions.")
    parser.add_argument("--browser-profile", default="openclaw-cws-publisher", help="OpenClaw browser profile.")
    parser.add_argument("--publish", action="store_true", help="Attempt browser-driven Chrome Web Store submission.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    dist = repo_root / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    run_step("generate_marketing_assets.py", "--repo-root", str(repo_root))
    run_step(
        "inventory_local_extensions.py",
        "--search-root",
        args.search_root,
        "--markdown-out",
        str(repo_root / "docs" / "local_extension_inventory.md"),
        "--json-out",
        str(dist / "local_extension_inventory.json"),
    )
    run_step(
        "build_extension_zip.py",
        "--extension-dir",
        str(repo_root / "extension"),
        "--out",
        str(dist / "locallens-extension.zip"),
    )
    run_step(
        "scan_publish_surface.py",
        "--root",
        str(repo_root),
        "--json-out",
        str(dist / "publish-surface.json"),
        "--markdown-out",
        str(repo_root / "docs" / "publish_surface.md"),
    )
    run_step(
        "generate_launch_manifest.py",
        "--repo-root",
        str(repo_root),
        "--out",
        str(dist / "launch-manifest.json"),
    )
    run_step(
        "generate_listing_copy.py",
        "--repo-root",
        str(repo_root),
        "--manifest",
        str(dist / "launch-manifest.json"),
        "--out",
        str(dist / "store-listing.json"),
    )
    run_step(
        "render_portfolio_entry.py",
        "--manifest",
        str(dist / "launch-manifest.json"),
        "--out",
        str(dist / "portfolio-entry.md"),
    )
    run_step(
        "render_release_notes.py",
        "--manifest",
        str(dist / "launch-manifest.json"),
        "--out",
        str(dist / "github-release-notes.md"),
    )
    run_step(
        "render_publish_commands.py",
        "--manifest",
        str(dist / "launch-manifest.json"),
        "--out",
        str(dist / "publish-commands.md"),
    )

    if args.publish:
        run_step(
            "publish_extension.py",
            "--repo-root",
            str(repo_root),
            "--manifest",
            str(dist / "launch-manifest.json"),
            "--listing",
            str(dist / "store-listing.json"),
            "--zip-path",
            str(dist / "locallens-extension.zip"),
            "--browser-profile",
            args.browser_profile,
        )

    print("Agent run completed.")


if __name__ == "__main__":
    main()
