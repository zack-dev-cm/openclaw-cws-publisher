from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skill" / "openclaw-cws-publisher" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_extension_zip import main as build_zip_main  # noqa: E402
from check_chrome_release import latest_release  # noqa: E402
from check_competitors import similarity  # noqa: E402
from check_design_gate import validate_report  # noqa: E402
from generate_launch_manifest import build_launch_manifest  # noqa: E402
from render_publish_commands import render_commands  # noqa: E402
from run_local_e2e_gates import discover_commands  # noqa: E402
from scan_publish_surface import scan  # noqa: E402
from validate_cws_package import validate as validate_cws_package  # noqa: E402


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
    assert "/Users/demo" not in findings[0]["excerpt"]
    assert "<redacted:absolute-path>" in findings[0]["excerpt"]


def test_scan_publish_surface_redacts_secret_like_excerpts(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    notes = tmp_path / "notes.md"
    fake_token = "ghp_" + "abcdefghijklmnopqrstuvwxyz123456"
    notes.write_text(f"token: {fake_token}\n", encoding="utf-8")
    subprocess.run(["git", "add", "notes.md"], cwd=tmp_path, check=True)

    findings = scan(tmp_path)

    assert findings == [
        {
            "kind": "token-shaped",
            "path": "notes.md",
            "line": 1,
            "excerpt": "token: <redacted:token>",
        }
    ]


def test_scan_publish_surface_checks_untracked_non_ignored_files(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    untracked = tmp_path / "draft.md"
    local_url = "http://local" + "host:3000"
    untracked.write_text(f"URL: {local_url}\n", encoding="utf-8")

    findings = scan(tmp_path)

    assert findings == [
        {
            "kind": "localhost-url",
            "path": "draft.md",
            "line": 1,
            "excerpt": "URL: <redacted:local-url>",
        }
    ]


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

    assert "## CWS Hardening Gates" in output
    assert "validate_cws_package.py" in output
    assert "check_design_gate.py" in output
    assert "check_chrome_release.py" in output
    assert "check_competitors.py" in output
    assert "## Reviewer Gate" in output
    assert "python3 scripts/reviewer_gate.py --repo-root . --skip-codex" in output
    assert "git config core.hooksPath .githooks" in output
    assert "git add <reviewed-files>" in output
    assert "git add ." not in output
    assert "--push" not in output


def test_render_publish_commands_pins_clawhub_cli() -> None:
    output = render_commands(
        {
            "repo_owner": "example-owner",
            "repo_name": "sample-extension",
            "github_description": "Sample extension",
            "github_homepage": "https://example.com",
            "github_topics": [],
            "release": {"tag": "v1.2.3", "title": "Release Sample Extension v1.2.3"},
            "clawhub": {
                "slug": "sample-extension",
                "name": "Sample Extension Skill",
                "version": "1.2.3",
                "tags": ["chrome-extension"],
            },
        }
    )

    assert "npx --yes clawhub@0.9.0 publish" in output


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


def write_zip_manifest(zip_path: Path, manifest: dict) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("assets/popup.js", "console.log('ok');")


def test_validate_cws_package_blocks_stale_host_permission_zip(tmp_path: Path) -> None:
    source_manifest = {
        "manifest_version": 3,
        "name": "Sample Extension",
        "version": "1.2.3",
        "description": "Sample description",
        "permissions": ["activeTab", "scripting", "storage"],
    }
    stale_manifest = {
        **source_manifest,
        "permissions": ["activeTab", "storage"],
        "host_permissions": ["https://example.com/*"],
        "content_scripts": [{"matches": ["https://example.com/*"], "js": ["assets/content.js"]}],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(source_manifest), encoding="utf-8")
    listing_path = tmp_path / "listing.json"
    listing_path.write_text(
        json.dumps(
            {
                "title": "Sample Extension",
                "summary": "Sample description",
                "detailed_description": "Sample Extension requests no persistent host permissions.",
                "permission_justifications": {
                    "activeTab": "Capture after user action.",
                    "scripting": "Inject after user action.",
                    "storage": "Store local settings.",
                },
                "host_permission_justifications": {},
                "privacy_practices": {"remote_code": False, "limited_use_certification": True},
            }
        ),
        encoding="utf-8",
    )
    zip_path = tmp_path / "dist" / "sample.zip"
    write_zip_manifest(zip_path, stale_manifest)

    report = validate_cws_package(
        SimpleNamespace(
            zip=str(zip_path),
            source_manifest=str(manifest_path),
            listing_json=str(listing_path),
            allow_host_permissions=False,
            json_out=None,
            markdown_out=None,
        )
    )

    assert not report["ok"]
    assert any("persistent host_permissions" in blocker for blocker in report["blockers"])
    assert any("does not match source manifest" in blocker for blocker in report["blockers"])


def test_validate_cws_package_accepts_no_host_active_tab_zip(tmp_path: Path) -> None:
    manifest = {
        "manifest_version": 3,
        "name": "Sample Extension",
        "version": "1.2.3",
        "description": "Sample description",
        "permissions": ["activeTab", "scripting", "storage"],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    listing_path = tmp_path / "listing.json"
    listing_path.write_text(
        json.dumps(
            {
                "title": "Sample Extension",
                "summary": "Sample description",
                "detailed_description": "Sample Extension requests no persistent host permissions.",
                "permission_justifications": {
                    "activeTab": "Capture after user action.",
                    "scripting": "Inject after user action.",
                    "storage": "Store local settings.",
                },
                "host_permission_justifications": {},
                "privacy_practices": {"remote_code": False, "limited_use_certification": True},
            }
        ),
        encoding="utf-8",
    )
    zip_path = tmp_path / "dist" / "sample.zip"
    write_zip_manifest(zip_path, manifest)

    report = validate_cws_package(
        SimpleNamespace(
            zip=str(zip_path),
            source_manifest=str(manifest_path),
            listing_json=str(listing_path),
            allow_host_permissions=False,
            json_out=None,
            markdown_out=None,
        )
    )

    assert report["ok"]


def test_design_gate_blocks_missing_or_low_scores() -> None:
    blockers = validate_report(
        {
            "surfaces": [
                {
                    "name": "popup",
                    "scores": {
                        "product_clarity": 9,
                        "visual_trust": 7,
                        "evidence_integrity": 9,
                        "responsive_polish": 9,
                        "accessibility": 9,
                        "claim_alignment": 9,
                    },
                }
            ]
        },
        threshold=8,
    )

    assert blockers == ["popup: visual_trust score 7 is below 8"]


def test_chrome_release_check_picks_highest_semver() -> None:
    release = latest_release(
        [
            {"version": "147.0.7727.56", "milestone": 147},
            {"version": "147.0.7727.102", "milestone": 147},
            {"version": "146.0.7680.180", "milestone": 146},
        ]
    )

    assert release["version"] == "147.0.7727.102"


def test_local_e2e_gate_discovers_package_scripts(tmp_path: Path) -> None:
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"check:cws": "node check.js", "test:e2e:reviewer": "python reviewer.py"}}),
        encoding="utf-8",
    )

    assert discover_commands(tmp_path) == [["pnpm", "check:cws"], ["pnpm", "test:e2e:reviewer"]]


def test_competitor_similarity_flags_close_positioning() -> None:
    assert similarity("ChatGPT exporter local markdown", "ChatGPT exporter local markdown") == 1.0
    assert similarity("ChatGPT exporter local markdown", "weather radar maps") == 0.0
