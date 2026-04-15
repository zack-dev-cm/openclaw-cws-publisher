# Publish Commands

## GitHub

```bash
git init
git add .
git commit -m "Initial public release: LocalLens: Private AI Summaries"
gh repo create zack-dev-cm/openclaw-cws-publisher --public --source=. --remote=origin --push
gh repo edit zack-dev-cm/openclaw-cws-publisher \
  --description "Chrome extension plus OpenClaw skill for packaging, leak-checking, and publishing LocalLens on the Chrome Web Store." \
  --homepage "https://clawhub.ai/zack-dev-cm/openclaw-cws-publisher"
gh repo edit zack-dev-cm/openclaw-cws-publisher --add-topic chrome-extension --add-topic chrome-web-store --add-topic openclaw --add-topic browser-automation --add-topic built-in-ai --add-topic privacy
gh release create v0.1.2 --title "Initial public release: LocalLens: Private AI Summaries" --notes-file dist/github-release-notes.md
```

## ClawHub

```bash
(cd skill/openclaw-cws-publisher && clawhub publish "$PWD" \
  --slug openclaw-cws-publisher \
  --name "OpenClaw CWS Publisher" \
  --version 0.1.2 \
  --changelog "Initial public release." \
  --tags "chrome-extension,chrome-web-store,openclaw,browser-automation,privacy")
```
