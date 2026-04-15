# Publish Commands

## GitHub

```bash
git init
git add .
git commit -m "Initial public release: LocalLens: Private AI Summaries"
gh repo create zack-dev-cm/openclaw-cws-publisher --public --source=. --remote=origin --push
gh release create v0.1.1 --title "Initial public release: LocalLens: Private AI Summaries" --notes-file dist/github-release-notes.md
```

## ClawHub

```bash
(cd skill/openclaw-cws-publisher && clawhub publish "$PWD" \
  --slug openclaw-cws-publisher \
  --name "OpenClaw CWS Publisher" \
  --version 0.1.1 \
  --changelog "Initial public release.")
```
