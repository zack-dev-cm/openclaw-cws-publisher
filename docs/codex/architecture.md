# Architecture

The repo has one public skill and a small set of local helper scripts.

## Boundaries

- `build_extension_zip.py`: creates the exact upload ZIP from a target extension directory.
- `validate_cws_package.py`: compares ZIP, source manifest, and listing JSON.
- `scan_publish_surface.py`: scans tracked plus untracked non-ignored public files and must redact matched values in reports.
- `run_local_e2e_gates.py`: discovers and runs repo-local checks only for the target repo named by the user.
- `generate_launch_manifest.py` and `render_publish_commands.py`: produce explicit metadata and commands; they do not publish automatically.

## Guardrails

- Extension product assets stay in the target extension repo.
- Generated `dist/` outputs are not source fixtures unless explicitly requested.
- Leak reports must never copy raw token-like values, local paths, or local endpoints.
- Publish commands are review artifacts, not automatic approval to release.

## Public Surface

Anything under `skill/openclaw-cws-publisher/`, top-level docs, tests, and CI is public-facing and must avoid private paths, secrets, dashboard dumps, and unsupported claims.
