# Changelog

## 0.2.2

- detect repo-local reviewer gates in launch metadata
- render reviewer-gate preflight commands before GitHub or ClawHub publish commands
- document the pending-review boundary so submitted Chrome Web Store drafts are not reset for nonblocking hardening

## 0.2.1

- add `--public-site-base` and `CWS_PUBLIC_SITE_BASE` support for reviewer-facing support, privacy-policy, and test-instructions links
- keep `github_homepage` pinned to the repo unless explicitly overridden
- add tests for the direct public-site-base argument and environment-based override path
