from __future__ import annotations

import json
import sys
import time

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skill" / "openclaw-cws-publisher" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_marketing_assets import asset_is_fresh
from inventory_local_extensions import collect_inventory
from publish_extension import dashboard_access_error, find_new_item_ref
from scan_publish_surface import scan


def test_inventory_filters_web_app_manifests(tmp_path: Path) -> None:
    web_app = tmp_path / "web" / "manifest.json"
    web_app.parent.mkdir(parents=True)
    web_app.write_text('{"name":"PWA","short_name":"PWA"}', encoding="utf-8")

    extension = tmp_path / "ext" / "manifest.json"
    extension.parent.mkdir(parents=True)
    extension.write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Real Extension",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )

    inventory = collect_inventory(tmp_path)
    assert len(inventory) == 1
    assert inventory[0]["name"] == "Real Extension"


def test_scan_publish_surface_flags_localhost(tmp_path: Path) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("Preview: http://localhost:3000 and ws://127.0.0.1:9000", encoding="utf-8")

    findings = scan(tmp_path)
    kinds = {finding["kind"] for finding in findings}
    assert "localhost-url" in kinds
    assert "websocket-url" in kinds


def test_inventory_detects_store_link_in_shipped_ui_asset(tmp_path: Path) -> None:
    extension = tmp_path / "repo" / "manifest.json"
    extension.parent.mkdir(parents=True)
    extension.write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Nested Link Extension",
                "version": "2.0.0",
            }
        ),
        encoding="utf-8",
    )
    popup_html = tmp_path / "repo" / "popup.html"
    popup_html.write_text(
        "https://chromewebstore.google.com/detail/example/abcdefghijklmnopqrstuvwxzyabcdef",
        encoding="utf-8",
    )

    inventory = collect_inventory(tmp_path)
    assert inventory[0]["published"] is True
    assert inventory[0]["store_links"]


def test_inventory_detects_cross_repo_store_link_hint(tmp_path: Path) -> None:
    repo_root = tmp_path / "plugin-repo"
    (repo_root / ".git").mkdir(parents=True)
    extension = repo_root / "extension" / "manifest.json"
    extension.parent.mkdir(parents=True)
    extension.write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Cross Repo Extension",
                "version": "3.0.0",
                "homepage_url": "https://github.com/example/plugin-repo",
            }
        ),
        encoding="utf-8",
    )
    portfolio_doc = tmp_path / "portfolio.github.io" / "projects" / "extension.md"
    portfolio_doc.parent.mkdir(parents=True)
    portfolio_doc.write_text(
        "Project: https://github.com/example/plugin-repo\nhttps://chromewebstore.google.com/detail/example/abcdefghijklmnopqrstuvwxzyabcdef",
        encoding="utf-8",
    )

    inventory = collect_inventory(tmp_path)
    assert inventory[0]["published"] is True
    assert inventory[0]["path"] == str(repo_root)
    assert inventory[0]["store_links"][0].startswith("https://chromewebstore.google.com/detail/")


def test_inventory_ignores_generic_nested_folder_name_for_global_hints(tmp_path: Path) -> None:
    repo_root = tmp_path / "my-real-project"
    (repo_root / ".git").mkdir(parents=True)
    extension = repo_root / "extension" / "manifest.json"
    extension.parent.mkdir(parents=True)
    extension.write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Nested Extension",
                "version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    portfolio_doc = tmp_path / "portfolio.github.io" / "projects" / "extension.md"
    portfolio_doc.parent.mkdir(parents=True)
    portfolio_doc.write_text(
        "extension\nhttps://chromewebstore.google.com/detail/example/abcdefghijklmnopqrstuvwxzyabcdef",
        encoding="utf-8",
    )

    inventory = collect_inventory(tmp_path)
    assert inventory[0]["published"] is False
    assert inventory[0]["path"] == str(repo_root)


def test_inventory_ignores_repo_docs_with_competitor_store_links(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo-with-research"
    (repo_root / ".git").mkdir(parents=True)
    extension = repo_root / "extension" / "manifest.json"
    extension.parent.mkdir(parents=True)
    extension.write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Research Extension",
                "version": "1.0.0",
                "homepage_url": "https://github.com/example/repo-with-research",
            }
        ),
        encoding="utf-8",
    )
    competitor_notes = repo_root / "docs" / "research.md"
    competitor_notes.parent.mkdir(parents=True)
    competitor_notes.write_text(
        "Competitor listing\nhttps://chromewebstore.google.com/detail/example/abcdefghijklmnopqrstuvwxzyabcdef",
        encoding="utf-8",
    )

    inventory = collect_inventory(tmp_path)
    assert inventory[0]["published"] is False
    assert inventory[0]["path"] == str(repo_root)


def test_asset_is_fresh_tracks_source_updates(tmp_path: Path) -> None:
    source = tmp_path / "marketing.html"
    css = tmp_path / "marketing.css"
    output = tmp_path / "out.png"
    source.write_text("<html></html>", encoding="utf-8")
    css.write_text("body{}", encoding="utf-8")
    output.write_text("png", encoding="utf-8")
    assert asset_is_fresh(output, [source, css]) is True

    time.sleep(0.01)
    css.write_text("body{color:red;}", encoding="utf-8")
    assert asset_is_fresh(output, [source, css]) is False


def test_publish_extension_rejects_storefront_redirect_snapshot() -> None:
    snapshot = """
- generic [ref=e1]:
  - banner [ref=e2]:
    - tab [selected] [ref=e56] [cursor=pointer]:
      - generic: Discover
  - main [ref=e62]:
    - heading [level=1] [ref=e63]: Welcome to Chrome Web Store
    - heading [level=2] [ref=e234]: Top categories
    - generic [ref=e181] [cursor=pointer]:
      - generic [ref=e182]: See collection
""".strip()

    assert find_new_item_ref(snapshot) is None
    assert dashboard_access_error(snapshot) == "storefront_redirect"


def test_publish_extension_accepts_dashboard_snapshot_with_new_item() -> None:
    snapshot = """
- generic [ref=e1]:
  - heading [level=1] [ref=e2]: Developer Dashboard
  - button [ref=e15] [cursor=pointer]:
    - generic [ref=e16]: Add new item
""".strip()

    assert find_new_item_ref(snapshot) == "e15"
    assert dashboard_access_error(snapshot) is None
