#!/usr/bin/env python3
"""PR の本文の先頭に「## 図」の節を置き、画像を GitHub にアップロードして貼る。

使い方:
  python3 attach.py <owner/repo> <PR 番号> <画像> [<画像> ...] [--alt "<説明>" ...] [--heading "<見出し>"]
    例: python3 attach.py octo-org/octo-shop 123 overview-123.png roadmap-123.png \\
          --alt "この PR の概要" --alt "PR の全体像（この PR の位置）"

- 本文に「## <見出し>」の節（既定は「## 図」）が既にあれば、その節（次の「## 」見出しの手前まで）を差し替える。ほかの節は変えない
- gh pr edit --attach で上げると、本文の ./<ファイル名> がアップロード先の URL に書き換わる
- 貼ったあとに本文を読み直し、画像のリンクがすべて user-attachments になったことを確かめる
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def pop_option(args: list[str], name: str) -> list[str]:
    values = []
    while name in args:
        i = args.index(name)
        if i + 1 >= len(args):
            sys.exit(f"{name} の後に値が要る")
        values.append(args[i + 1])
        del args[i:i + 2]
    return values


def main():
    args = sys.argv[1:]
    alts = pop_option(args, "--alt")
    headings = pop_option(args, "--heading")
    heading = headings[-1] if headings else "図"
    if len(args) < 3:
        sys.exit(__doc__)
    repo, number, images = args[0], args[1], [Path(p).resolve() for p in args[2:]]
    folder = images[0].parent
    if any(p.parent != folder for p in images):
        sys.exit("画像は同じフォルダに置く（本文の ./<ファイル名> をそのフォルダから解決するため）")

    body = gh("pr", "view", number, "-R", repo, "--json", "body", "--jq", ".body")
    lines = [f"![{alts[i] if i < len(alts) else p.stem}](./{p.name})" for i, p in enumerate(images)]
    section = f"## {heading}\n\n" + "\n\n".join(lines) + "\n\n"
    head_re = rf"^## {re.escape(heading)}\n"
    if re.search(head_re, body, flags=re.M):
        body = re.sub(head_re + r".*?(?=^## |\Z)", lambda _: section, body, count=1, flags=re.M | re.S)
    else:
        body = section + body

    with tempfile.NamedTemporaryFile("w", suffix=".md", dir=folder, delete=False, encoding="utf-8") as f:
        f.write(body)
        body_file = f.name
    cmd = ["pr", "edit", number, "-R", repo, "--body-file", body_file]
    for p in images:
        cmd += ["--attach", f"./{p.name}"]
    try:
        subprocess.run(["gh", *cmd], check=True, cwd=folder, stdout=subprocess.DEVNULL)
    finally:
        Path(body_file).unlink(missing_ok=True)

    after = gh("pr", "view", number, "-R", repo, "--json", "body", "--jq", ".body")
    m = re.search(head_re + r"(.*?)(?=^## |\Z)", after, flags=re.M | re.S)
    links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", m.group(1) if m else after)
    bad = [l for l in links if "user-attachments" not in l]
    print("\n".join(links))
    if bad:
        sys.exit(f"アップロードされていない画像のリンクがある: {bad}")


if __name__ == "__main__":
    main()
