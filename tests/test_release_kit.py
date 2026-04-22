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
from render_publish_commands import render_commands  # noqa: E402
from scan_publish_surface import scan  # noqa: E402


def test_scan_publish_surface_checks_tracked_dist_files(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    readme = tmp_path / "README.md"
    readme.write_text("hello\n", encoding="utf-8")
    leaked = tmp_path / "dist" / "artifact.txt"
    leaked.parent.mkdir(parents=True)
    fake_path = "/".join(["", "Users", "demo", "secret"])
    leaked.write_text(f"path: {fake_path}\n", encoding="utf-8")
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
        public_site_base=None,
        topics=None,
        tags=None,
    )

    assert payload["repo_url"] == "https://github.com/example-owner/sample-extension"
    assert payload["github_description"].startswith("Package, scan, and release Sample Extension")
    assert payload["clawhub"]["tags"] == ["chrome-extension", "chrome-web-store", "openclaw"]
    assert payload["support_url"].endswith("/issues")
    assert payload["reviewer_gate"] == {"detected": False, "script": "", "pre_push_hook": ""}


def test_build_launch_manifest_prefers_public_site_base_for_reviewer_links(tmp_path: Path) -> None:
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

    payload = build_launch_manifest(
        repo_root,
        owner="example-owner",
        extension_manifest=None,
        clawhub_slug=None,
        clawhub_name=None,
        github_description=None,
        github_homepage=None,
        public_site_base="https://sample-extension.pages.dev",
        topics=None,
        tags=None,
    )

    assert payload["github_homepage"] == "https://github.com/example-owner/sample-extension"
    assert payload["support_url"] == "https://sample-extension.pages.dev/support/"
    assert payload["privacy_policy_url"] == "https://sample-extension.pages.dev/privacy/"
    assert payload["test_instructions_url"] == "https://sample-extension.pages.dev/support/#reviewer-checklist"


def test_build_launch_manifest_uses_public_site_base_env_for_reviewer_links(tmp_path: Path, monkeypatch) -> None:
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
    monkeypatch.setenv("CWS_PUBLIC_SITE_BASE", "https://sample-extension.workers.dev")

    payload = build_launch_manifest(
        repo_root,
        owner="example-owner",
        extension_manifest=None,
        clawhub_slug=None,
        clawhub_name=None,
        github_description=None,
        github_homepage=None,
        public_site_base=None,
        topics=None,
        tags=None,
    )

    assert payload["github_homepage"] == "https://github.com/example-owner/sample-extension"
    assert payload["support_url"] == "https://sample-extension.workers.dev/support/"
    assert payload["privacy_policy_url"] == "https://sample-extension.workers.dev/privacy/"
    assert payload["test_instructions_url"] == "https://sample-extension.workers.dev/support/#reviewer-checklist"


def test_build_launch_manifest_detects_reviewer_gate(tmp_path: Path) -> None:
    repo_root = tmp_path / "sample-extension"
    extension_dir = repo_root / "extension"
    extension_dir.mkdir(parents=True)
    (repo_root / "scripts").mkdir()
    (repo_root / ".githooks").mkdir()
    (repo_root / "scripts" / "reviewer_gate.py").write_text("print('gate')\n", encoding="utf-8")
    (repo_root / ".githooks" / "pre-push").write_text("#!/bin/sh\n", encoding="utf-8")
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

    payload = build_launch_manifest(
        repo_root,
        owner="example-owner",
        extension_manifest=None,
        clawhub_slug=None,
        clawhub_name=None,
        github_description=None,
        github_homepage=None,
        public_site_base=None,
        topics=None,
        tags=None,
    )

    assert payload["reviewer_gate"] == {
        "detected": True,
        "script": "scripts/reviewer_gate.py",
        "pre_push_hook": ".githooks/pre-push",
    }


def test_render_publish_commands_includes_reviewer_gate_preflight() -> None:
    output = render_commands(
        {
            "repo_owner": "example-owner",
            "repo_name": "sample-extension",
            "github_description": "Sample extension",
            "github_homepage": "https://example.com",
            "github_topics": ["chrome-extension"],
            "release": {"tag": "v1.2.3", "title": "Release Sample Extension v1.2.3"},
            "reviewer_gate": {
                "detected": True,
                "script": "scripts/reviewer_gate.py",
                "pre_push_hook": ".githooks/pre-push",
            },
        }
    )

    assert "## Reviewer Gate" in output
    assert "python3 scripts/reviewer_gate.py --repo-root . --skip-codex" in output
    assert "git config core.hooksPath .githooks" in output


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
