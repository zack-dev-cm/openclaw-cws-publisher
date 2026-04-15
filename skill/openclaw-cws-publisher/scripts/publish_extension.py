from __future__ import annotations

import argparse
from pathlib import Path

from common import abs_path, load_json
from openclaw_bridge import (
    OpenClawError,
    arm_upload,
    click,
    dump_snapshot_text,
    fill_fields,
    find_ref,
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
SIGN_IN_MARKERS = ("sign in", "signin", "google account")


def find_new_item_ref(snapshot_text: str) -> str | None:
    return find_ref(snapshot_text, ["add", "new", "item"]) or find_ref(snapshot_text, ["new", "item"])


def dashboard_access_error(snapshot_text: str) -> str | None:
    lowered = snapshot_text.lower()
    if any(marker in lowered for marker in SIGN_IN_MARKERS):
        return "signed_out"
    if find_new_item_ref(snapshot_text):
        return None
    if any(marker in lowered for marker in PUBLIC_STORE_MARKERS):
        return "storefront_redirect"
    return None


def fill_text_field(profile: str, snap: str, label_phrases: list[str], value: str) -> bool:
    ref = find_ref(snap, label_phrases)
    if not ref:
        return False
    fill_fields(profile, [{"ref": ref, "type": "textbox", "value": value}])
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a Chrome extension package through OpenClaw browser automation.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--listing", required=True, help="Listing copy JSON.")
    parser.add_argument("--zip-path", required=True, help="Extension ZIP path.")
    parser.add_argument("--browser-profile", required=True, help="OpenClaw browser profile.")
    parser.add_argument("--dashboard-url", default=DASHBOARD_URL, help="Chrome Web Store dashboard URL override.")
    parser.add_argument("--dry-run", action="store_true", help="Stop after dashboard inspection.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    launch_manifest = load_json(args.manifest)
    listing = load_json(args.listing)
    zip_path = abs_path(args.zip_path)
    profile = args.browser_profile

    snapshot_dir = repo_root / "dist" / "openclaw"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    try:
        start_browser(profile)
        open_url(profile, args.dashboard_url)
        wait_for(profile, ms=7000)
        first_snapshot = snapshot(profile)
        dump_snapshot_text(first_snapshot, snapshot_dir / "dashboard-initial.txt")

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

        add_ref = find_new_item_ref(first_snapshot)
        if not add_ref:
            raise SystemExit(
                "Could not find the New Item control in the dashboard snapshot. "
                f"Review {snapshot_dir / 'dashboard-initial.txt'}."
            )

        click(profile, add_ref)
        wait_for(profile, ms=5000)
        upload_snapshot = snapshot(profile)
        dump_snapshot_text(upload_snapshot, snapshot_dir / "dashboard-upload.txt")

        upload_ref = (
            find_ref(upload_snapshot, ["upload", "zip"])
            or find_ref(upload_snapshot, ["select", "file"])
            or find_ref(upload_snapshot, ["browse"])
        )
        if not upload_ref:
            raise SystemExit(
                "Could not find the ZIP upload control after opening the new item flow. "
                f"Review {snapshot_dir / 'dashboard-upload.txt'}."
            )

        arm_upload(profile, zip_path)
        click(profile, upload_ref)
        wait_for(profile, ms=8000)

        listing_snapshot = snapshot(profile)
        dump_snapshot_text(listing_snapshot, snapshot_dir / "dashboard-listing.txt")

        if "summary" in listing_snapshot.lower():
            fill_text_field(profile, listing_snapshot, ["summary"], listing["short_description"])
        if "description" in listing_snapshot.lower():
            fill_text_field(profile, listing_snapshot, ["description"], listing["detailed_description"])
        if launch_manifest["extension"]["name"].lower() in listing_snapshot.lower():
            pass
        else:
            fill_text_field(profile, listing_snapshot, ["name"], listing["name"])

        print("OpenClaw reached the listing form and attempted to fill visible text fields.")
        print(f"Snapshots saved under {snapshot_dir}")
    except OpenClawError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
