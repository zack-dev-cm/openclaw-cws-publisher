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
    github_description = manifest.get("github_description", "")
    github_homepage = manifest.get("github_homepage", "")
    github_topics = manifest.get("github_topics", [])
    clawhub = manifest["clawhub"]
    release = manifest["release"]
    tags = clawhub.get("tags", [])

    topic_flags = " ".join(f"--add-topic {topic}" for topic in github_topics)
    tag_flags = f' \\\n  --tags "{",".join(tags)}"' if tags else ""

    text = f"""# Publish Commands

## GitHub

```bash
git init
git add .
git commit -m "{release['title']}"
gh repo create zack-dev-cm/{repo_name} --public --source=. --remote=origin --push
gh repo edit zack-dev-cm/{repo_name} \\
  --description "{github_description}" \\
  --homepage "{github_homepage}"
gh repo edit zack-dev-cm/{repo_name} {topic_flags}
gh release create {release['tag']} --title "{release['title']}" --notes-file dist/github-release-notes.md
```

## ClawHub

```bash
(cd skill/openclaw-cws-publisher && clawhub publish "$PWD" \\
  --slug {clawhub['slug']} \\
  --name "{clawhub['name']}" \\
  --version {clawhub['version']} \\
  --changelog "Initial public release."{tag_flags})
```
"""
    dump_text(args.out, text)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
