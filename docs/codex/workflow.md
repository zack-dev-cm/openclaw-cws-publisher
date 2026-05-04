# Workflow

## Default Loop

1. Restate the release goal and verification.
2. Identify the target extension repo and the specific helper being changed.
3. Make the smallest code or docs change.
4. Run focused tests, then the public-surface gate.
5. Update release docs only when the workflow or invariant changed.

## Release Kit Flow

1. Build the ZIP intended for upload.
2. Validate ZIP, source manifest, listing copy, and privacy contract.
3. Scan tracked files for leak risks with redacted report excerpts.
4. Run repo-local reviewer or E2E gates.
5. Check design evidence, Chrome Stable freshness, and competitor positioning.
6. Generate launch metadata and render publish commands.

## Parallel Work

Use subagents only when the user explicitly asks for delegation. Keep ownership disjoint: one agent per helper, docs area, or review surface.
