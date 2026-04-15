# AGENTS

## Scope

This repo is the public release kit for Chrome extension repos. It is not the place to ship a specific extension product, store screenshots, or browser-profile automation.

## Deployment Rules

When preparing a release from this repo:

1. Keep product assets in the target extension repo.
2. Run the leak scan against tracked files before generating publish commands.
3. Set GitHub description, homepage, and topics explicitly. Do not leave repo metadata blank.
4. Set ClawHub tags explicitly on every publish. Do not rely on inherited `latest` only.
5. Keep GitHub topics and ClawHub tags aligned in the generated manifest.
6. Do not commit generated `dist/` outputs or audit reports unless the user explicitly wants checked-in examples.
7. Do not add arbitrary filesystem inventory or logged-in browser automation to the public skill surface.

## Required Metadata

- GitHub description
- GitHub homepage
- GitHub topics
- ClawHub slug
- ClawHub name
- ClawHub tags

## Separation Rules

- Extension product repos stay separate from this release-kit repo.
- Browser automation for Chrome Web Store dashboards is operator-only and must not be bundled into the public ClawHub skill.
