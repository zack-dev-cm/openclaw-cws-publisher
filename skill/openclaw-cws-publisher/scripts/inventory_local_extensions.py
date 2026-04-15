from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from common import abs_path, dump_json, dump_text, markdown_table


STORE_LINK_RE = re.compile(
    r"https://chromewebstore\.google\.com/detail/[^/\s)]+/(?P<id>[a-z]{32})",
    re.IGNORECASE,
)


def find_store_links(repo_root: Path) -> list[str]:
    links: list[str] = []
    candidate_paths = set()
    for pattern in ["README*", "PRIVACY*", "*.md"]:
        candidate_paths.update(path for path in repo_root.glob(pattern) if path.is_file())
    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        candidate_paths.update(path for path in docs_dir.glob("*.md") if path.is_file())

    for path in sorted(candidate_paths):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        links.extend(match.group(0) for match in STORE_LINK_RE.finditer(text))
    return sorted(set(links))


def collect_inventory(search_root: Path) -> list[dict]:
    inventory: list[dict] = []
    try:
        result = subprocess.run(
            [
                "find",
                str(search_root),
                "-maxdepth",
                "4",
                "-name",
                "manifest.json",
                "-not",
                "-path",
                "*/node_modules/*",
                "-not",
                "-path",
                "*/dist/*",
                "-not",
                "-path",
                "*/build/*",
                "-not",
                "-path",
                "*/.venv/*",
                "-print",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        manifest_paths = [Path(line) for line in result.stdout.splitlines() if line.strip()]
    except FileNotFoundError:
        manifest_paths = list(search_root.rglob("manifest.json"))

    for manifest_path in sorted(manifest_paths):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if "manifest_version" not in manifest:
            continue
        repo_root = manifest_path.parent
        store_links = find_store_links(repo_root)
        inventory.append(
            {
                "name": manifest.get("name", repo_root.name),
                "version": str(manifest.get("version", "")),
                "path": str(repo_root),
                "description": manifest.get("description", ""),
                "permissions": manifest.get("permissions", []),
                "store_links": store_links,
                "published": bool(store_links),
            }
        )
    inventory.sort(key=lambda item: (not item["published"], item["name"].lower(), item["path"]))
    return inventory


def render_markdown(search_root: Path, inventory: list[dict]) -> str:
    rows = []
    for item in inventory:
        links = "<br>".join(item["store_links"]) if item["store_links"] else "local only"
        rows.append(
            [
                item["name"],
                "published" if item["published"] else "unpublished",
                item["version"] or "-",
                links,
                item["path"],
            ]
        )

    return "\n".join(
        [
            "# Local Chrome Extension Inventory",
            "",
            f"Search root: `{search_root}`",
            "",
            markdown_table(["Name", "Status", "Version", "Store Link", "Path"], rows),
            "",
            f"Total extension repos found: **{len(inventory)}**",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan a filesystem tree for Chrome extension manifests and inferred store links.")
    parser.add_argument("--search-root", required=True, help="Filesystem root to scan.")
    parser.add_argument("--json-out", required=True, help="JSON output path.")
    parser.add_argument("--markdown-out", required=True, help="Markdown output path.")
    args = parser.parse_args()

    search_root = abs_path(args.search_root)
    inventory = collect_inventory(search_root)
    dump_json(args.json_out, inventory)
    dump_text(args.markdown_out, render_markdown(search_root, inventory))
    print(f"Scanned {len(inventory)} extension repos under {search_root}")


if __name__ == "__main__":
    main()
