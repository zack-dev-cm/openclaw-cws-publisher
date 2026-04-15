from __future__ import annotations

import json
import sys

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skill" / "openclaw-cws-publisher" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from inventory_local_extensions import collect_inventory
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
