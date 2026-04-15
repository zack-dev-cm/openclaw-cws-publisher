from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import abs_path, load_json
from openclaw_bridge import (
    OpenClawError,
    arm_upload,
    click,
    dump_snapshot_text,
    fill_fields,
    find_ref,
    line_element,
    line_ref,
    open_url,
    snapshot,
    start_browser,
    wait_for,
)


DASHBOARD_URL = "https://chrome.google.com/webstore/devconsole"
PUBLIC_STORE_MARKERS = (
    "welcome to chrome web store",
    "top categories",
    "see collection",
    "favorites of 2025",
)
BLOCKER_PATTERNS = (" is required", "must certify", "must provide")
DEFAULT_REVIEWER_NOTES = [
    "Use Chrome 138+ on desktop with Chrome built-in AI enabled.",
    "Open a text-heavy page and run Summarize page from the LocalLens popup.",
    "Highlight text and verify Summarize selection, Simplify selection, Translate selection, and Safe-share selection.",
]


def has_sign_in_control(snapshot_text: str) -> bool:
    for line in snapshot_text.splitlines():
        lowered = line.lower()
        if "sign in" not in lowered and "signin" not in lowered and "log in" not in lowered:
            continue
        if "[cursor=pointer]" in lowered or find_ref(line, ["sign", "in"]) or find_ref(line, ["log", "in"]):
            return True
    return False


def find_new_item_ref(snapshot_text: str) -> str | None:
    return find_ref(snapshot_text, ["add", "new", "item"]) or find_ref(snapshot_text, ["new", "item"])


def find_upload_new_package_ref(snapshot_text: str) -> str | None:
    return find_button_ref(snapshot_text, ["upload", "new", "package"])


def find_upload_ref(snapshot_text: str) -> str | None:
    return (
        find_ref(snapshot_text, ["button", "select", "file"])
        or find_ref(snapshot_text, ["button", "browse"])
        or find_ref(snapshot_text, ["button", "upload", "zip"])
        or find_ref(snapshot_text, ["select", "file"])
        or find_ref(snapshot_text, ["browse"])
        or find_ref(snapshot_text, ["upload", "zip"])
    )


def has_upload_dialog(snapshot_text: str) -> bool:
    lowered = snapshot_text.lower()
    return "select file" in lowered and ("dialog" in lowered or "upload new package" in lowered)


def find_button_ref(snapshot_text: str, label_phrases: list[str]) -> str | None:
    return find_ref(snapshot_text, ["button", *label_phrases]) or find_ref(snapshot_text, label_phrases)


def find_link_ref(snapshot_text: str, label_phrases: list[str]) -> str | None:
    return find_ref(snapshot_text, ["link", *label_phrases]) or find_ref(snapshot_text, label_phrases)


def find_textbox_ref(snapshot_text: str, label_phrases: list[str]) -> str | None:
    return find_ref(snapshot_text, ["textbox", *label_phrases])


def find_combobox_ref(snapshot_text: str, label_phrases: list[str]) -> str | None:
    return find_ref(snapshot_text, ["combobox", *label_phrases]) or find_ref(snapshot_text, label_phrases)


def find_option_ref(snapshot_text: str, option_label: str) -> str | None:
    return find_ref(snapshot_text, ["option", option_label]) or find_ref(snapshot_text, [option_label])


def find_checkbox_ref(snapshot_text: str, label_phrases: list[str]) -> str | None:
    return find_ref(snapshot_text, ["checkbox", *label_phrases]) or find_ref(snapshot_text, label_phrases)


def find_radio_ref(snapshot_text: str, label_phrases: list[str]) -> str | None:
    return find_ref(snapshot_text, ["radio", *label_phrases]) or find_ref(snapshot_text, label_phrases)


def line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def matching_line_indices(snapshot_text: str, label_phrases: list[str]) -> list[int]:
    lowered_phrases = [phrase.lower() for phrase in label_phrases]
    return [
        index
        for index, line in enumerate(snapshot_text.splitlines())
        if all(phrase in line.lower() for phrase in lowered_phrases)
    ]


def control_is_checked(snapshot_text: str, label_phrases: list[str]) -> bool:
    lines = snapshot_text.splitlines()
    for index in matching_line_indices(snapshot_text, label_phrases):
        line = lines[index].lower()
        if ("checkbox" in line or "radio" in line) and "[checked]" in line:
            return True
    return False


def combobox_has_value(snapshot_text: str, label_phrases: list[str], value: str) -> bool:
    lowered_value = value.lower()
    for index in matching_line_indices(snapshot_text, label_phrases):
        line = snapshot_text.splitlines()[index].lower()
        if "combobox" in line and lowered_value in line:
            return True
    return False


def find_section_button_ref(snapshot_text: str, label_phrases: list[str]) -> str | None:
    lines = snapshot_text.splitlines()
    stack: list[tuple[int, str, str | None]] = []
    lowered_phrases = [phrase.lower() for phrase in label_phrases]

    for index, line in enumerate(lines):
        indent = line_indent(line)
        while stack and indent <= stack[-1][0]:
            stack.pop()

        element = line_element(line)
        ref = line_ref(line)
        if ref:
            stack.append((indent, ref, element))

        lowered = line.lower()
        if not all(phrase in lowered for phrase in lowered_phrases):
            continue

        ancestor_nodes = stack[:-1] if ref else stack
        for ancestor_indent, _, _ in reversed(ancestor_nodes):
            candidate_buttons: list[tuple[str, str]] = []
            for candidate in lines[index + 1 :]:
                candidate_indent = line_indent(candidate)
                if candidate_indent <= ancestor_indent:
                    break
                if not candidate.lstrip().lower().startswith("- button"):
                    continue
                candidate_ref = line_ref(candidate)
                if candidate_ref:
                    candidate_buttons.append((candidate_ref, candidate.lower()))
            upload_candidates = [
                candidate_ref
                for candidate_ref, candidate_line in candidate_buttons
                if any(token in candidate_line for token in ("drop", "select", "upload", "browse"))
                and "remove image" not in candidate_line
            ]
            if upload_candidates:
                return upload_candidates[0]
            safe_candidates = [
                candidate_ref
                for candidate_ref, candidate_line in candidate_buttons
                if "remove image" not in candidate_line
            ]
            if safe_candidates:
                return safe_candidates[0]
    return None


def dashboard_access_error(snapshot_text: str) -> str | None:
    lowered = snapshot_text.lower()
    if has_sign_in_control(snapshot_text):
        return "signed_out"
    if find_new_item_ref(snapshot_text):
        return None
    if any(marker in lowered for marker in PUBLIC_STORE_MARKERS):
        return "storefront_redirect"
    return None


def fill_text_field(profile: str, snap: str, label_phrases: list[str], value: str) -> bool:
    ref = find_textbox_ref(snap, label_phrases)
    if not ref:
        return False
    fill_fields(profile, [{"ref": ref, "type": "textbox", "value": value}])
    return True


def capture_snapshot(profile: str, snapshot_dir: Path, filename: str) -> str:
    snap = snapshot(profile)
    dump_snapshot_text(snap, snapshot_dir / filename)
    return snap


def upload_asset(profile: str, snap: str, label_phrases: list[str], asset_path: str | None) -> bool:
    if not asset_path:
        return False
    ref = find_section_button_ref(snap, label_phrases) or find_button_ref(snap, label_phrases)
    if not ref:
        return False
    arm_upload(profile, asset_path)
    click(profile, ref)
    return True


def navigate_to_section(profile: str, snap: str, label_phrases: list[str], snapshot_dir: Path, filename: str) -> str:
    ref = find_link_ref(snap, label_phrases)
    if not ref:
        raise SystemExit(f"Could not find section link matching {' '.join(label_phrases)}.")
    click(profile, ref)
    wait_for(profile, ms=4000)
    return capture_snapshot(profile, snapshot_dir, filename)


def select_combobox_option(
    profile: str,
    snap: str,
    label_phrases: list[str],
    option_label: str,
    snapshot_dir: Path,
    before_filename: str,
    after_filename: str,
) -> str:
    if not option_label or combobox_has_value(snap, label_phrases, option_label):
        return snap
    ref = find_combobox_ref(snap, label_phrases)
    if not ref:
        return snap
    click(profile, ref)
    wait_for(profile, ms=2000)
    options_snapshot = capture_snapshot(profile, snapshot_dir, before_filename)
    option_ref = find_option_ref(options_snapshot, option_label)
    if not option_ref:
        raise SystemExit(f"Could not find option '{option_label}' for {' '.join(label_phrases)}.")
    click(profile, option_ref)
    wait_for(profile, ms=2000)
    return capture_snapshot(profile, snapshot_dir, after_filename)


def ensure_checkbox(profile: str, snap: str, label_phrases: list[str], snapshot_dir: Path, filename: str) -> str:
    if control_is_checked(snap, label_phrases):
        return snap
    ref = find_checkbox_ref(snap, label_phrases)
    if not ref:
        raise SystemExit(f"Could not find checkbox matching {' '.join(label_phrases)}.")
    click(profile, ref)
    wait_for(profile, ms=1500)
    return capture_snapshot(profile, snapshot_dir, filename)


def ensure_radio(profile: str, snap: str, label_phrases: list[str], snapshot_dir: Path, filename: str) -> str:
    if control_is_checked(snap, label_phrases):
        return snap
    ref = find_radio_ref(snap, label_phrases)
    if not ref:
        raise SystemExit(f"Could not find radio matching {' '.join(label_phrases)}.")
    click(profile, ref)
    wait_for(profile, ms=1500)
    return capture_snapshot(profile, snapshot_dir, filename)


def upload_package(profile: str, snap: str, zip_path: Path, snapshot_dir: Path, version: str) -> str:
    upload_button = find_upload_new_package_ref(snap)
    if upload_button:
        click(profile, upload_button)
        wait_for(profile, ms=2000)
        snap = capture_snapshot(profile, snapshot_dir, "dashboard-upload.txt")

    upload_ref = find_upload_ref(snap)
    if not upload_ref:
        raise SystemExit("Could not find the ZIP upload control.")

    arm_upload(profile, zip_path)
    click(profile, upload_ref)
    for _ in range(15):
        wait_for(profile, ms=5000)
        snap = capture_snapshot(profile, snapshot_dir, "dashboard-package.txt")
        if f"Version {version}" in snap or (not has_upload_dialog(snap) and "Permissions" in snap):
            return snap
    raise SystemExit("ZIP upload did not complete.")


def create_new_draft(profile: str, snap: str, zip_path: Path, snapshot_dir: Path, version: str) -> str:
    add_ref = find_new_item_ref(snap)
    if not add_ref:
        raise SystemExit(
            "Could not find the New Item control in the dashboard snapshot. "
            f"Review {snapshot_dir / 'dashboard-initial.txt'}."
        )

    click(profile, add_ref)
    wait_for(profile, ms=5000)
    upload_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-upload.txt")
    return upload_package(profile, upload_snapshot, zip_path, snapshot_dir, version)


def ensure_listing(
    profile: str,
    snap: str,
    launch_manifest: dict,
    listing: dict,
    snapshot_dir: Path,
) -> str:
    listing_snapshot = navigate_to_section(profile, snap, ["store", "listing"], snapshot_dir, "dashboard-listing.txt")
    homepage_url = launch_manifest.get("repo_url", "")
    support_url = listing.get("support_url") or launch_manifest.get("support_url") or homepage_url

    if "description" in listing_snapshot.lower():
        fill_text_field(profile, listing_snapshot, ["description"], listing["detailed_description"])
        wait_for(profile, ms=2000)
        listing_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-listing.txt")

    listing_snapshot = select_combobox_option(
        profile,
        listing_snapshot,
        ["category"],
        listing.get("category", ""),
        snapshot_dir,
        "category-options.txt",
        "after-category.txt",
    )
    listing_snapshot = select_combobox_option(
        profile,
        listing_snapshot,
        ["language"],
        listing.get("language", ""),
        snapshot_dir,
        "language-options.txt",
        "after-language.txt",
    )

    if homepage_url:
        fill_text_field(profile, listing_snapshot, ["homepage", "url"], homepage_url)
        wait_for(profile, ms=1500)
        listing_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-listing.txt")
    if support_url:
        fill_text_field(profile, listing_snapshot, ["support", "url"], support_url)
        wait_for(profile, ms=1500)
        listing_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-listing.txt")

    store_assets = listing.get("store_assets", {})
    for label_phrases, asset_path in [
        (["store", "icon"], store_assets.get("icon")),
        (["small", "promo", "tile"], store_assets.get("promo_small")),
        (["marquee", "promo", "tile"], store_assets.get("promo_marquee")),
    ]:
        if upload_asset(profile, listing_snapshot, label_phrases, asset_path):
            wait_for(profile, ms=5000)
            listing_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-listing.txt")

    for asset_path in store_assets.get("screenshots", []):
        if upload_asset(profile, listing_snapshot, ["screenshots"], asset_path):
            wait_for(profile, ms=5000)
            listing_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-listing.txt")

    save_ref = find_button_ref(listing_snapshot, ["save", "draft"])
    if save_ref:
        click(profile, save_ref)
        wait_for(profile, ms=4000)
        listing_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-listing.txt")
    return listing_snapshot


def ensure_privacy(
    profile: str,
    snap: str,
    listing: dict,
    snapshot_dir: Path,
) -> str:
    privacy_snapshot = navigate_to_section(profile, snap, ["privacy"], snapshot_dir, "dashboard-privacy.txt")
    privacy = listing.get("privacy", {})
    permission_justifications = privacy.get("permission_justifications", {})

    fill_text_field(profile, privacy_snapshot, ["single", "purpose", "description"], listing["single_purpose"])
    wait_for(profile, ms=1500)
    privacy_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-privacy.txt")

    for permission, justification in permission_justifications.items():
        if fill_text_field(profile, privacy_snapshot, [permission, "justification"], justification):
            wait_for(profile, ms=1500)
            privacy_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-privacy.txt")

    privacy_snapshot = ensure_radio(
        profile,
        privacy_snapshot,
        ["no", "i", "am", "not", "using", "remote", "code"],
        snapshot_dir,
        "dashboard-privacy.txt",
    )

    for category in privacy.get("data_categories", []):
        privacy_snapshot = ensure_checkbox(
            profile,
            privacy_snapshot,
            category.lower().split(),
            snapshot_dir,
            "dashboard-privacy.txt",
        )

    privacy_policy_url = privacy.get("privacy_policy_url")
    if privacy_policy_url:
        fill_text_field(profile, privacy_snapshot, ["privacy", "policy", "url"], privacy_policy_url)
        wait_for(profile, ms=1500)
        privacy_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-privacy.txt")

    for certification in privacy.get("certifications", []):
        important_words = re.sub(r"[^a-z0-9 ]+", "", certification.lower()).split()
        privacy_snapshot = ensure_checkbox(
            profile,
            privacy_snapshot,
            important_words[:10],
            snapshot_dir,
            "dashboard-privacy.txt",
        )

    save_ref = find_button_ref(privacy_snapshot, ["save", "draft"])
    if save_ref:
        click(profile, save_ref)
        wait_for(profile, ms=4000)
        privacy_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-privacy.txt")
    return privacy_snapshot


def extract_submit_blockers(snapshot_text: str) -> list[str]:
    blockers: list[str] = []
    for line in snapshot_text.splitlines():
        lowered = line.lower()
        if not any(pattern in lowered for pattern in BLOCKER_PATTERNS):
            continue
        match = re.search(r":\s*(.+)$", line)
        message = match.group(1).strip().strip('"') if match else line.strip().lstrip("-").strip()
        if message not in blockers:
            blockers.append(message)
    return blockers


def validate_submission_readiness(profile: str, snap: str, snapshot_dir: Path) -> tuple[str, list[str]]:
    why_ref = find_button_ref(snap, ["why", "can't", "i", "submit"])
    if not why_ref:
        return snap, []
    click(profile, why_ref)
    wait_for(profile, ms=2000)
    blocker_snapshot = capture_snapshot(profile, snapshot_dir, "submit-blockers.txt")
    return blocker_snapshot, extract_submit_blockers(blocker_snapshot)


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a Chrome extension package through OpenClaw browser automation.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--listing", required=True, help="Listing copy JSON.")
    parser.add_argument("--zip-path", required=True, help="Extension ZIP path.")
    parser.add_argument("--browser-profile", required=True, help="OpenClaw browser profile.")
    parser.add_argument("--dashboard-url", default=DASHBOARD_URL, help="Chrome Web Store dashboard URL override.")
    parser.add_argument("--dry-run", action="store_true", help="Stop after dashboard inspection.")
    parser.add_argument("--submit", action="store_true", help="Submit the draft for review after blockers are cleared.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    launch_manifest = load_json(args.manifest)
    listing = load_json(args.listing)
    zip_path = abs_path(args.zip_path)
    profile = args.browser_profile
    version = launch_manifest["extension"]["version"]

    snapshot_dir = repo_root / "dist" / "openclaw"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    try:
        start_browser(profile)
        open_url(profile, args.dashboard_url)
        wait_for(profile, ms=7000)
        first_snapshot = capture_snapshot(profile, snapshot_dir, "dashboard-initial.txt")

        dashboard_error = dashboard_access_error(first_snapshot)
        if dashboard_error == "signed_out":
            raise SystemExit(
                "Chrome Web Store dashboard is not signed in for this OpenClaw profile. "
                f"Review {snapshot_dir / 'dashboard-initial.txt'} and log in, then rerun publish_extension.py."
            )
        if dashboard_error == "storefront_redirect":
            raise SystemExit(
                "Chrome Web Store developer dashboard did not open for this OpenClaw profile. "
                "Google redirected the session to the public store homepage instead. "
                f"Review {snapshot_dir / 'dashboard-initial.txt'}, confirm the profile is signed into the correct "
                "developer account, then rerun publish_extension.py."
            )

        if args.dry_run:
            print(f"Saved dashboard snapshot to {snapshot_dir / 'dashboard-initial.txt'}")
            return

        current_snapshot = first_snapshot
        if find_upload_new_package_ref(current_snapshot):
            current_snapshot = upload_package(profile, current_snapshot, zip_path, snapshot_dir, version)
        elif find_new_item_ref(current_snapshot):
            current_snapshot = create_new_draft(profile, current_snapshot, zip_path, snapshot_dir, version)
        elif "Permissions" in current_snapshot and find_upload_ref(current_snapshot):
            current_snapshot = upload_package(profile, current_snapshot, zip_path, snapshot_dir, version)

        listing_snapshot = ensure_listing(profile, current_snapshot, launch_manifest, listing, snapshot_dir)
        privacy_snapshot = ensure_privacy(profile, listing_snapshot, listing, snapshot_dir)
        blocker_snapshot, blockers = validate_submission_readiness(profile, privacy_snapshot, snapshot_dir)
        if blockers:
            raise SystemExit("Draft still has Chrome Web Store blockers:\n- " + "\n- ".join(blockers))

        if args.submit:
            submit_ref = find_button_ref(blocker_snapshot, ["submit", "for", "review"])
            if submit_ref and "[disabled]" not in blocker_snapshot.lower():
                click(profile, submit_ref)
                wait_for(profile, ms=4000)
                capture_snapshot(profile, snapshot_dir, "submit-review.txt")

        print("OpenClaw updated the package, store listing, and privacy form for the Chrome Web Store draft.")
        print(f"Snapshots saved under {snapshot_dir}")
    except OpenClawError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
