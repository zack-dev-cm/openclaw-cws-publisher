from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skill" / "openclaw-cws-publisher" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import openclaw_bridge


def completed(cmd: list[str], *, returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)


def test_invoke_with_retry_passes_browser_timeout_and_retries(monkeypatch) -> None:
    calls: list[tuple[list[str], int | None]] = []

    def fake_run(cmd: list[str], *, timeout: int | None = None, cwd=None, env=None):
        calls.append((cmd, timeout))
        if len(calls) == 1:
            return completed(cmd, returncode=1, stderr="Error: gateway timeout after 20000ms")
        return completed(cmd, stdout="ok")

    monkeypatch.setattr(openclaw_bridge, "run", fake_run)
    monkeypatch.setattr(openclaw_bridge.time, "sleep", lambda _: None)

    result = openclaw_bridge.invoke_with_retry("gmail-worker", "snapshot", "--format", "ai", timeout=90_000, retries=1)

    assert result == "ok"
    assert len(calls) == 2
    assert calls[0][0][:6] == ["openclaw", "browser", "--browser-profile", "gmail-worker", "--timeout", "90000"]
    assert calls[0][1] == 105


def test_snapshot_uses_retryable_invoke(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_invoke(profile: str, *args: str, timeout: int = 0, retries: int = 0, retry_delay_ms: int = 0) -> str:
        captured["profile"] = profile
        captured["args"] = args
        captured["timeout"] = timeout
        captured["retries"] = retries
        captured["retry_delay_ms"] = retry_delay_ms
        return "snapshot"

    monkeypatch.setattr(openclaw_bridge, "invoke_with_retry", fake_invoke)

    out_path = tmp_path / "snapshot.txt"
    assert openclaw_bridge.snapshot("publisher", out=out_path) == "snapshot"
    assert captured == {
        "profile": "publisher",
        "args": ("snapshot", "--format", "ai", "--limit", "400", "--out", str(out_path)),
        "timeout": 120_000,
        "retries": 2,
        "retry_delay_ms": 2_000,
    }


def test_stage_upload_file_copies_into_openclaw_upload_dir(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "bundle.zip"
    source.write_text("zip", encoding="utf-8")

    upload_root = tmp_path / "tmp" / "openclaw" / "uploads"

    real_path = openclaw_bridge.Path

    def fake_path(value="."):
        if value == "/tmp/openclaw/uploads":
            return upload_root
        return real_path(value)

    monkeypatch.setattr(openclaw_bridge, "Path", fake_path)

    staged = openclaw_bridge.stage_upload_file(source)

    assert staged == upload_root / "bundle.zip"
    assert staged.read_text(encoding="utf-8") == "zip"
