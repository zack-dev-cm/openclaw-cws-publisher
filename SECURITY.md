# Security

This repository publishes a local release-kit skill. It does not run a hosted
service, but generated reports and publish commands can affect public release
surfaces.

## Supported Versions

Security fixes are applied to the latest default-branch release line.

## Report A Vulnerability

Until a dedicated security contact exists, use a private GitHub security
advisory for this repository.

Include:

- affected file or helper
- reproduction steps
- whether a generated report copied sensitive data
- whether public GitHub or ClawHub metadata was affected

## Sensitive Data Policy

Do not publish raw tokens, private paths, local endpoints, private dashboard
captures, account identifiers, or customer data. Leak reports must redact matched
values while preserving enough context to fix the source file.
