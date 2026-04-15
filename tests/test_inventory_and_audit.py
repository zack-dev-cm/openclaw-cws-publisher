from __future__ import annotations

import json
import sys
import time

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skill" / "openclaw-cws-publisher" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_launch_manifest import build_launch_manifest
from generate_listing_copy import build_listing_payload
from generate_marketing_assets import asset_is_fresh
from inventory_local_extensions import collect_inventory
from publish_extension import (
    extract_submit_blockers,
    dashboard_access_error,
    find_button_ref,
    find_checkbox_ref,
    find_combobox_ref,
    find_new_item_ref,
    find_option_ref,
    find_radio_ref,
    find_section_button_ref,
    find_textbox_ref,
    find_upload_ref,
    has_sign_in_control,
    has_upload_dialog,
)
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


def test_build_launch_manifest_adds_support_and_policy_urls(tmp_path: Path) -> None:
    repo_root = tmp_path / "sample-extension"
    extension_dir = repo_root / "extension"
    extension_dir.mkdir(parents=True)
    (extension_dir / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Sample Extension",
                "version": "1.2.3",
                "description": "Sample description",
            }
        ),
        encoding="utf-8",
    )

    payload = build_launch_manifest(repo_root)
    assert payload["repo_url"] == "https://github.com/zack-dev-cm/sample-extension"
    assert payload["support_url"] == "https://github.com/zack-dev-cm/sample-extension/issues"
    assert payload["privacy_policy_url"].endswith("/docs/privacy-policy.md")
    assert payload["test_instructions_url"].endswith("/docs/test-instructions.md")
    assert payload["extension"]["category"] == "Tools"


def test_build_listing_payload_matches_manifest_permissions_and_assets(tmp_path: Path) -> None:
    repo_root = tmp_path / "sample-extension"
    extension_dir = repo_root / "extension"
    extension_dir.mkdir(parents=True)
    (extension_dir / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "Sample Extension",
                "version": "1.2.3",
                "description": "Sample description",
                "permissions": ["activeTab", "scripting"],
            }
        ),
        encoding="utf-8",
    )

    launch_manifest = build_launch_manifest(repo_root)
    payload = build_listing_payload(repo_root, launch_manifest)

    assert payload["category"] == "Tools"
    assert payload["language"] == "English"
    assert set(payload["privacy"]["permission_justifications"]) == {"activeTab", "scripting"}
    assert "storage" not in payload["privacy"]["permission_justifications"]
    assert payload["privacy"]["data_categories"] == ["Website content"]
    assert payload["privacy"]["privacy_policy_url"] == launch_manifest["privacy_policy_url"]
    assert len(payload["store_assets"]["screenshots"]) == 2
    assert payload["store_assets"]["screenshots"][1].endswith("locallens-store-screenshot-2.jpg")
    assert payload["store_assets"]["promo_marquee"].endswith("locallens-promo-marquee.jpg")


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


def test_publish_extension_ignores_google_account_menu_on_valid_dashboard() -> None:
    snapshot = """
- generic [ref=e2]:
  - button "Google Account: Re Dream (kaisenaiko@gmail.com)" [ref=e33] [cursor=pointer]:
    - img [ref=e35]
  - button "Add a new item" [ref=e72]:
    - generic [ref=e76]: New item
""".strip()

    assert has_sign_in_control(snapshot) is False
    assert dashboard_access_error(snapshot) is None


def test_publish_extension_detects_explicit_sign_in_control() -> None:
    snapshot = """
- generic [ref=e1]:
  - link "Sign in" [ref=e12] [cursor=pointer]:
    - /url: https://accounts.google.com/signin
""".strip()

    assert has_sign_in_control(snapshot) is True
    assert dashboard_access_error(snapshot) == "signed_out"


def test_publish_extension_prefers_select_file_button_in_upload_dialog() -> None:
    snapshot = """
- dialog "Add new item" [active] [ref=e213]:
  - generic [ref=e217]:
    - paragraph [ref=e218]: Drop a ZIP or CRX file here or select a file
    - button "Select file" [ref=e220]:
      - generic [ref=e223]: Select file
""".strip()

    assert find_upload_ref(snapshot) == "e220"
    assert find_button_ref(snapshot, ["select", "file"]) == "e220"
    assert has_upload_dialog(snapshot) is True


def test_publish_extension_prefers_textbox_for_description_field() -> None:
    snapshot = """
- generic [ref=e313]:
  - paragraph [ref=e314]: Summary from package
- generic [ref=e317]:
  - generic [ref=e320]:
    - textbox "Description*" [ref=e323]:
      - /placeholder: ""
""".strip()

    assert find_textbox_ref(snapshot, ["description"]) == "e323"


def test_publish_extension_finds_graphic_asset_buttons_and_select_inputs() -> None:
    snapshot = """
- generic [ref=e209]:
  - generic [ref=e210]:
    - generic [ref=e211]:
      - paragraph [ref=e212]: Small promo tile
    - generic [ref=e369]:
      - button [ref=e522] [cursor=pointer]:
        - img [ref=e374]
  - generic [ref=e227]:
    - generic [ref=e228]:
      - paragraph [ref=e229]: Marquee promo tile
    - button [ref=e524] [cursor=pointer]:
      - img [ref=e239]
      - paragraph [ref=e242]: Drop image here
- generic [ref=e300]:
  - generic [ref=e301]:
    - paragraph [ref=e302]: Screenshots *
  - generic [ref=e303]:
    - button "Remove image Screenshot 1" [ref=e304] [cursor=pointer]:
      - img [ref=e305]
    - img "Screenshot 1" [ref=e306]
  - button "Screenshots * Drop image here" [ref=e307] [cursor=pointer]:
    - img [ref=e308]
    - paragraph [ref=e309]: Drop image here
- generic [ref=e141]:
  - combobox "Category* Select a category" [expanded] [ref=e142] [cursor=pointer]:
    - generic: Category*
  - listbox "Category" [ref=e380]:
    - option "Tools" [ref=e387] [cursor=pointer]:
      - generic: Tools
""".strip()

    assert find_section_button_ref(snapshot, ["small", "promo", "tile"]) == "e522"
    assert find_section_button_ref(snapshot, ["marquee", "promo", "tile"]) == "e524"
    assert find_section_button_ref(snapshot, ["screenshots"]) == "e307"
    assert find_combobox_ref(snapshot, ["category"]) == "e142"
    assert find_option_ref(snapshot, "Tools") == "e387"


def test_publish_extension_extracts_privacy_controls_and_blockers() -> None:
    privacy_snapshot = """
- generic [ref=e179]:
  - generic [ref=e180]: Are you using remote code?
  - generic [ref=e182]:
    - generic [ref=e183]:
      - radiogroup [ref=e184]:
        - generic [ref=e185]:
          - radio "No, I am not using Remote code" [ref=e188] [cursor=pointer]
          - generic [ref=e191]: No, I am not using Remote code
    - generic [ref=e276]:
      - generic [ref=e277] [cursor=pointer]:
        - checkbox "Website content" [ref=e278]
        - generic:
          - img
    - generic [ref=e286]:
      - generic [ref=e287] [cursor=pointer]:
        - checkbox "I do not sell or transfer user data to third parties, outside of the approved use cases" [ref=e288]
        - generic:
          - img
""".strip()
    blocker_snapshot = """
- generic [ref=e510]:
  - paragraph [ref=e511]: A justification for activeTab is required.
  - paragraph [ref=e512]: The single purpose description is required.
""".strip()

    assert find_radio_ref(privacy_snapshot, ["no", "remote", "code"]) == "e188"
    assert find_checkbox_ref(privacy_snapshot, ["website", "content"]) == "e278"
    assert find_checkbox_ref(blocker_snapshot + "\n" + privacy_snapshot, ["sell", "or", "transfer", "user", "data"]) == "e288"
    assert extract_submit_blockers(blocker_snapshot) == [
        "A justification for activeTab is required.",
        "The single purpose description is required.",
    ]
