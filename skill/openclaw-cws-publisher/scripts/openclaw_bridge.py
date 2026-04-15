from __future__ import annotations

import json
import math
import re
import shutil
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
    return invoke_with_retry(profile, *args, timeout=timeout)


def is_retryable_error(message: str) -> bool:
    lowered = message.lower()
    return "gateway timeout" in lowered or "timed out" in lowered


def invoke_with_retry(
    profile: str,
    *args: str,
    timeout: int = 60_000,
    retries: int = 0,
    retry_delay_ms: int = 1_500,
) -> str:
    cmd = ["openclaw", "browser", "--browser-profile", profile, "--timeout", str(timeout), *args]
    process_timeout = max(5, math.ceil(timeout / 1000) + 15)
    last_error: OpenClawError | None = None
    for attempt in range(retries + 1):
        try:
            result = run(cmd, timeout=process_timeout)
        except subprocess.TimeoutExpired as error:
            last_error = OpenClawError(f"OpenClaw command timed out after {process_timeout}s: {' '.join(cmd)}")
        else:
            if result.returncode == 0:
                return result.stdout
            last_error = OpenClawError(result.stderr or result.stdout or "OpenClaw command failed")

        if attempt == retries or last_error is None or not is_retryable_error(str(last_error)):
            raise last_error
        time.sleep(retry_delay_ms / 1000)

    raise last_error or OpenClawError("OpenClaw command failed")


def start_browser(profile: str) -> None:
    status = browser_status(profile)
    if status.get("running"):
        return
    invoke_with_retry(profile, "start", timeout=180_000, retries=1, retry_delay_ms=3_000)


def open_url(profile: str, url: str) -> None:
    invoke_with_retry(profile, "open", url, timeout=120_000, retries=1)


def navigate(profile: str, url: str) -> None:
    invoke_with_retry(profile, "navigate", url, timeout=120_000, retries=1)


def wait_for(profile: str, *, text: str | None = None, ms: int = 5000) -> None:
    if text:
        invoke_with_retry(profile, "wait", "--text", text, "--timeout", str(ms), timeout=ms + 30_000, retries=1)
    else:
        time.sleep(max(ms, 0) / 1000)


def snapshot(profile: str, out: Path | None = None) -> str:
    args = ["snapshot", "--format", "ai", "--limit", "400"]
    if out is not None:
        args += ["--out", str(abs_path(out))]
    return invoke_with_retry(profile, *args, timeout=120_000, retries=2, retry_delay_ms=2_000)


def stage_upload_file(file_path: str | Path) -> Path:
    source = abs_path(file_path)
    upload_dir = Path("/tmp/openclaw/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / source.name
    if source != target:
        shutil.copy2(source, target)
    return target


def arm_upload(profile: str, file_path: str | Path) -> None:
    staged_path = stage_upload_file(file_path)
    invoke_with_retry(profile, "upload", str(staged_path), timeout=120_000, retries=1)


def click(profile: str, ref: str) -> None:
    invoke(profile, "click", ref)


def type_text(profile: str, ref: str, text: str) -> None:
    invoke(profile, "type", ref, text)


def fill_fields(profile: str, fields: list[dict]) -> None:
    invoke(profile, "fill", "--fields", json.dumps(fields))


def browser_status(profile: str) -> dict:
    try:
        return json.loads(invoke_with_retry(profile, "status", "--json", timeout=45_000, retries=1))
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
