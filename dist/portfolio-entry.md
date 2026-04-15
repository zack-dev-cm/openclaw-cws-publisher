# OpenClaw CWS Publisher + LocalLens

> Privacy-first Chrome extension and OpenClaw publishing agent for local AI summaries.

## Summary
This project pairs a user-facing Chrome extension with an operator-facing release agent. `LocalLens` summarizes, simplifies, translates, and safe-shares page text locally with Chrome built-in AI. `OpenClaw CWS Publisher` inventories local extension repos, generates store assets, scans for leak risks, builds the extension ZIP, and drives Chrome Web Store submission through OpenClaw browser automation.

## Project Link
https://zack-dev-cm.github.io/projects/locallens-private-ai-summaries.md

## Key Features
- Local-first page and selection summaries with Chrome built-in AI
- Safe-share mode that redacts obvious sensitive strings before local AI processing
- OpenClaw publish agent for Chrome Web Store packaging, dashboard automation, and release metadata generation
- Leak-scan workflow before GitHub, ClawHub, and Chrome Web Store release

## Tech Stack
- Chrome Extension (Manifest V3)
- JavaScript
- Python
- OpenClaw
- ClawHub
- GitHub CLI

## Benchmarks & Analytics
- Extension version: 0.1.1
- Chrome minimum version: 138
- Runtime surfaces: 4 (extension, GitHub, ClawHub, portfolio)
- Privacy posture: local-only text processing

## Links
- [View on GitHub](https://github.com/zack-dev-cm/openclaw-cws-publisher)
- [Open on ClawHub](https://clawhub.ai/zack-dev-cm/openclaw-cws-publisher)
