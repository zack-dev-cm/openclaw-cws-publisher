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
REJECTED_PARENT_NAMES = {
    "web",
    "public",
    "static",
    "build",
    ".vite",
    "cache",
    "datasets",
    "fixtures",
    "outputs",
    "docs",
}


def _extract_store_links(candidate_paths: list[Path]) -> list[str]:
    links: list[str] = []
    for path in sorted(set(candidate_paths)):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        links.extend(match.group(0) for match in STORE_LINK_RE.finditer(text))
    return sorted(set(links))


def _find_repo_local_store_links(repo_root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            [
                "rg",
                "-l",
                "chromewebstore\\.google\\.com/detail/",
                "--glob",
                "README*",
                "--glob",
                "PRIVACY*",
                "--glob",
                "CHANGELOG*",
                "--glob",
                "*.html",
                "--glob",
                "*.js",
                "--glob",
                "*.jsx",
                "--glob",
                "*.mjs",
                "--glob",
                "*.cjs",
                "--glob",
                "*.ts",
                "--glob",
                "*.tsx",
                "--glob",
                "*.json",
                "--glob",
                "!node_modules/**",
                "--glob",
                "!dist/**",
                "--glob",
                "!build/**",
                "--glob",
                "!.venv/**",
                "--glob",
                "!docs/**",
                "--glob",
                "!tests/**",
                str(repo_root),
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        return [Path(line) for line in result.stdout.splitlines() if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        candidate_paths = []
        for pattern in [
            "README*",
            "PRIVACY*",
            "CHANGELOG*",
            "*.html",
            "*.js",
            "*.jsx",
            "*.mjs",
            "*.cjs",
            "*.ts",
            "*.tsx",
            "*.json",
        ]:
            candidate_paths.extend(path for path in repo_root.rglob(pattern) if path.is_file())
        return [
            path
            for path in candidate_paths
            if all(part not in {"node_modules", "dist", "build", ".venv", "docs", "tests"} for part in path.parts)
        ]


def _find_global_store_link_hints(search_root: Path, identifiers: list[str]) -> list[Path]:
    search_targets = [path for path in search_root.iterdir() if path.is_dir() and path.name.endswith(".github.io")]
    if not search_targets:
        return []
    candidate_paths: list[Path] = []
    for identifier in identifiers:
        if not identifier or identifier.startswith("__MSG_"):
            continue
        try:
            result = subprocess.run(
                [
                    "rg",
                    "-l",
                    "-F",
                    identifier,
                    "--glob",
                    "*.md",
                    "--glob",
                    "README*",
                    "--glob",
                    "!node_modules/**",
                    "--glob",
                    "!dist/**",
                    "--glob",
                    "!build/**",
                    "--glob",
                    "!.venv/**",
                    *[str(path) for path in search_targets],
                ],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        candidate_paths.extend(Path(line) for line in result.stdout.splitlines() if line.strip())
    return candidate_paths


def resolve_project_root(manifest_path: Path, search_root: Path) -> Path:
    current = manifest_path.parent.resolve()
    search_root = search_root.resolve()
    while True:
        if (current / ".git").exists():
            return current
        if current == search_root or search_root not in current.parents:
            return manifest_path.parent.resolve()
        current = current.parent


def build_global_identifiers(repo_name: str, homepage_url: str | None) -> list[str]:
    identifiers: list[str] = []
    if homepage_url and homepage_url.startswith(("https://", "http://")):
        identifiers.append(homepage_url.rstrip("/"))
    if repo_name and any(char in repo_name for char in "-_."):
        identifiers.append(repo_name)
    return identifiers


def find_store_links(
    repo_root: Path,
    search_root: Path,
    *,
    repo_name: str,
    homepage_url: str | None,
) -> list[str]:
    repo_local_paths = _find_repo_local_store_links(repo_root)
    links = _extract_store_links(repo_local_paths)
    if links:
        return links

    global_paths = _find_global_store_link_hints(search_root, build_global_identifiers(repo_name, homepage_url))
    return _extract_store_links(global_paths)


def looks_like_extension_manifest(manifest_path: Path) -> bool:
    lowered_parts = {part.lower() for part in manifest_path.parts}
    parent_name = manifest_path.parent.name.lower()
    if parent_name in REJECTED_PARENT_NAMES:
        return False
    if any(part in REJECTED_PARENT_NAMES for part in lowered_parts):
        return "chrome-extension" in lowered_parts or "extension" in lowered_parts
    return True


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
            timeout=20,
        )
        manifest_paths = [Path(line) for line in result.stdout.splitlines() if line.strip()]
    except FileNotFoundError:
        patterns = ["manifest.json", "*/manifest.json", "*/*/manifest.json", "*/*/*/manifest.json", "*/*/*/*/manifest.json"]
        manifest_paths = sorted({path for pattern in patterns for path in search_root.glob(pattern) if path.is_file()})
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Timed out while scanning for manifest.json files under {search_root}") from exc

    for manifest_path in sorted(manifest_paths):
        if not looks_like_extension_manifest(manifest_path):
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if "manifest_version" not in manifest:
            continue
        repo_root = resolve_project_root(manifest_path, search_root)
        store_links = find_store_links(
            repo_root,
            search_root,
            repo_name=repo_root.name,
            homepage_url=manifest.get("homepage_url"),
        )
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
