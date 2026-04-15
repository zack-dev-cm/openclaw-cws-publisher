from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

from common import abs_path, run


class OpenClawError(RuntimeError):
    pass


REF_PATTERNS = [r"^\[([a-z]?\d+)\]", r"\bref[:= ]([a-z]?\d+)\b", r"\(([a-z]?\d+)\)"]
INTERACTIVE_ELEMENTS = {
    "button",
    "checkbox",
    "combobox",
    "link",
    "menuitem",
    "option",
    "radio",
    "switch",
    "tab",
    "textbox",
}


def invoke(profile: str, *args: str, timeout: int = 60_000) -> str:
    cmd = ["openclaw", "browser", "--browser-profile", profile, *args]
    try:
        result = run(cmd, timeout=max(5, timeout // 1000))
    except subprocess.TimeoutExpired as error:
        raise OpenClawError(f"OpenClaw command timed out after {max(5, timeout // 1000)}s: {' '.join(cmd)}") from error
    if result.returncode != 0:
        raise OpenClawError(result.stderr or result.stdout or "OpenClaw command failed")
    return result.stdout


def start_browser(profile: str) -> None:
    status = browser_status(profile)
    if status.get("running"):
        return
    invoke(profile, "start", timeout=180_000)


def open_url(profile: str, url: str) -> None:
    invoke(profile, "open", url)


def navigate(profile: str, url: str) -> None:
    invoke(profile, "navigate", url)


def wait_for(profile: str, *, text: str | None = None, ms: int = 5000) -> None:
    if text:
        invoke(profile, "wait", "--text", text, "--timeout", str(ms))
    else:
        time.sleep(max(ms, 0) / 1000)


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


def fill_fields(profile: str, fields: list[dict]) -> None:
    invoke(profile, "fill", "--fields", json.dumps(fields))


def browser_status(profile: str) -> dict:
    try:
        return json.loads(invoke(profile, "status", "--json", timeout=30_000))
    except (OpenClawError, json.JSONDecodeError):
        return {}


def line_ref(line: str) -> str | None:
    for pattern in REF_PATTERNS:
        match = re.search(pattern, line)
        if match:
            return match.group(1)
    return None


def line_element(line: str) -> str | None:
    stripped = line.strip()
    match = re.match(r"^- ([^\[:]+)", stripped)
    return match.group(1).strip().lower() if match else None


def find_ref(snapshot_text: str, phrases: list[str]) -> str | None:
    lines = snapshot_text.splitlines()
    stack: list[tuple[int, str, str | None]] = []
    for line in lines:
        indent = len(line) - len(line.lstrip(" "))
        while stack and indent <= stack[-1][0]:
            stack.pop()

        element = line_element(line)
        ref = line_ref(line)
        if ref:
            stack.append((indent, ref, element))

        lowered = line.lower()
        if not all(phrase.lower() in lowered for phrase in phrases):
            continue

        if ref and element in INTERACTIVE_ELEMENTS:
            return ref

        ancestor_nodes = stack[:-1] if ref else stack
        for _, ancestor_ref, ancestor_element in reversed(ancestor_nodes):
            if ancestor_element in INTERACTIVE_ELEMENTS:
                return ancestor_ref

        if ref:
            return ref
        if stack:
            return stack[-1][1]
    return None


def dump_snapshot_text(snapshot_text: str, path: str | Path) -> None:
    abs_path(path).write_text(snapshot_text, encoding="utf-8")
