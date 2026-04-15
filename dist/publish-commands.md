# Publish Commands

## GitHub

```bash
git init
git add .
git commit -m "Initial public release: LocalLens: Private AI Summaries"
gh repo create zack-dev-cm/openclaw-cws-publisher --public --source=. --remote=origin --push
gh release create v0.1.0 --title "Initial public release: LocalLens: Private AI Summaries" --notes-file dist/github-release-notes.md
```

## ClawHub

```bash
clawhub publish ./skill/openclaw-cws-publisher \
  --slug openclaw-cws-publisher \
  --name "OpenClaw CWS Publisher" \
  --version 0.1.0 \
  --changelog "Initial public release."
```
