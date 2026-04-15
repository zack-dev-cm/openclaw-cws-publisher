from __future__ import annotations

import json
import re
from pathlib import Path

from common import abs_path, run


class OpenClawError(RuntimeError):
    pass


def invoke(profile: str, *args: str, timeout: int = 60_000) -> str:
    cmd = ["openclaw", "browser", "--browser-profile", profile, *args]
    result = run(cmd, timeout=max(5, timeout // 1000))
    if result.returncode != 0:
        raise OpenClawError(result.stderr or result.stdout or "OpenClaw command failed")
    return result.stdout


def start_browser(profile: str) -> None:
    invoke(profile, "start")


def open_url(profile: str, url: str) -> None:
    invoke(profile, "open", url)


def navigate(profile: str, url: str) -> None:
    invoke(profile, "navigate", url)


def wait_for(profile: str, *, text: str | None = None, ms: int = 5000) -> None:
    if text:
        invoke(profile, "wait", "--text", text, "--timeout", str(ms))
    else:
        invoke(profile, "wait", "--time", str(ms))


def snapshot(profile: str, out: Path | None = None) -> str:
    cmd = ["openclaw", "browser", "--browser-profile", profile, "snapshot", "--format", "ai", "--limit", "400"]
    if out is not None:
        cmd += ["--out", str(abs_path(out))]
    result = run(cmd, timeout=60)
    if result.returncode != 0:
        raise OpenClawError(result.stderr or result.stdout or "OpenClaw snapshot failed")
    return result.stdout


def arm_upload(profile: str, file_path: str | Path) -> None:
    invoke(profile, "upload", str(abs_path(file_path)))


def click(profile: str, ref: str) -> None:
    invoke(profile, "click", ref)


def type_text(profile: str, ref: str, text: str) -> None:
    invoke(profile, "type", ref, text)


def find_ref(snapshot_text: str, phrases: list[str]) -> str | None:
    lines = snapshot_text.splitlines()
    for line in lines:
        lowered = line.lower()
        if not all(phrase.lower() in lowered for phrase in phrases):
            continue
        for pattern in [r"^\[(\d+)\]", r"\bref[:= ](\d+)\b", r"\((\d+)\)"]:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
    return None


def dump_snapshot_text(snapshot_text: str, path: str | Path) -> None:
    abs_path(path).write_text(snapshot_text, encoding="utf-8")
