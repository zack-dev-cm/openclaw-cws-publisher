from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skill" / "openclaw-cws-publisher" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_extension_zip import main as build_zip_main  # noqa: E402
from generate_launch_manifest import build_launch_manifest  # noqa: E402
from scan_publish_surface import scan  # noqa: E402


def test_scan_publish_surface_checks_tracked_dist_files(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    readme = tmp_path / "README.md"
    readme.write_text("hello\n", encoding="utf-8")
    leaked = tmp_path / "dist" / "artifact.txt"
    leaked.parent.mkdir(parents=True)
    leaked.write_text("path: /Users/zack/secret\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md", "dist/artifact.txt"], cwd=tmp_path, check=True)

    findings = scan(tmp_path)
    assert findings
    assert findings[0]["path"] == "dist/artifact.txt"
    assert findings[0]["kind"] == "absolute-path"


def test_build_launch_manifest_is_generic(tmp_path: Path) -> None:
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
                "minimum_chrome_version": "138",
            }
        ),
        encoding="utf-8",
    )

    payload = build_launch_manifest(
        repo_root,
        owner="example-owner",
        extension_manifest=None,
        clawhub_slug="sample-extension",
        clawhub_name="Sample Extension Skill",
        github_description=None,
        github_homepage=None,
        topics=None,
        tags=None,
    )

    assert payload["repo_url"] == "https://github.com/example-owner/sample-extension"
    assert payload["github_description"].startswith("Package, scan, and release Sample Extension")
    assert payload["clawhub"]["tags"] == ["chrome-extension", "chrome-web-store", "openclaw"]
    assert payload["support_url"].endswith("/issues")


def test_build_extension_zip_writes_relative_archive(tmp_path: Path, monkeypatch) -> None:
    extension_dir = tmp_path / "extension"
    extension_dir.mkdir()
    (extension_dir / "manifest.json").write_text('{"manifest_version": 3}', encoding="utf-8")
    (extension_dir / "popup.html").write_text("<html></html>", encoding="utf-8")
    out_path = tmp_path / "dist" / "extension.zip"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_extension_zip.py",
            "--extension-dir",
            str(extension_dir),
            "--out",
            str(out_path),
        ],
    )
    build_zip_main()

    with zipfile.ZipFile(out_path) as archive:
        assert sorted(archive.namelist()) == ["manifest.json", "popup.html"]
