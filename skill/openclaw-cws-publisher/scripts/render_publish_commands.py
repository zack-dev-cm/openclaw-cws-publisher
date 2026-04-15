from __future__ import annotations

import argparse

from common import dump_text, load_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Render GitHub and ClawHub publish commands from the launch manifest.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Markdown output path.")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    repo_name = manifest["repo_name"]
    clawhub = manifest["clawhub"]
    release = manifest["release"]

    text = f"""# Publish Commands

## GitHub

```bash
git init
git add .
git commit -m "{release['title']}"
gh repo create zack-dev-cm/{repo_name} --public --source=. --remote=origin --push
gh release create {release['tag']} --title "{release['title']}" --notes-file dist/github-release-notes.md
```

## ClawHub

```bash
clawhub publish ./skill/openclaw-cws-publisher \\
  --slug {clawhub['slug']} \\
  --name "{clawhub['name']}" \\
  --version {clawhub['version']} \\
  --changelog "Initial public release."
```
"""
    dump_text(args.out, text)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
