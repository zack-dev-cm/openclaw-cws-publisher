# Changelog

## 0.3.2

- scan tracked plus untracked non-ignored files before rendering publish guidance
- render reviewed-file staging instead of `git add .`
- remove auto-push from generated repo-creation commands
- pin the generated ClawHub CLI publish command

## 0.3.1

- redact secret-like, local-path, and local-endpoint matches in publish-surface reports
- add regression coverage so leak scans do not create new copies of detected tokens

## 0.3.0

- add exact ZIP/source-manifest/listing validation for stale package, permission, privacy, and remote-code drift
- add local reviewer/E2E gate discovery for CWS package, public-page, visual, and reviewer tests
- add design/UI/UX critic-score gate with screenshot metadata checks
- add current Chrome Stable release checks from the Chrome for Testing last-known-good feed
- add lightweight competitor and differentiation checks for risky listing claims
- document the activeTab-first, no-stale-ZIP, design-evidence, and latest-Chrome operating order

## 0.2.2

- detect repo-local reviewer gates in launch metadata
- render reviewer-gate preflight commands before GitHub or ClawHub publish commands
- document the pending-review boundary so submitted Chrome Web Store drafts are not reset for nonblocking hardening

## 0.2.1

- add `--public-site-base` and `CWS_PUBLIC_SITE_BASE` support for reviewer-facing support, privacy-policy, and test-instructions links
- keep `github_homepage` pinned to the repo unless explicitly overridden
- add tests for the direct public-site-base argument and environment-based override path
