#!/usr/bin/env python3
"""HTML を Chrome の headless で PNG にし、下の余白を切り詰める。

使い方:
  python3 render.py <html> [<html> ...]
    → 同じ場所に <名前>.png を書く（2 倍の解像度）。幅は HTML の body の width に合わせる

HTML が参照する CSS（common.css・overview.css・components.css）と JS（arrows.js）が無ければ、スキルの assets からコピーする。
Chrome の場所は環境変数 CHROME_PATH で渡せる。無ければよくある場所と PATH から探す。
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
]
ASSETS = Path(__file__).resolve().parent.parent / "assets"
TALL = 1600  # 描くときの窓の高さ（CSS px）。中身がこれより長いと切れる
MARGIN = 72  # 切り詰めたあとに残す下の余白（2 倍の画素）


def find_chrome() -> str:
    env = os.environ.get("CHROME_PATH")
    if env:
        return env
    for c in CHROME_CANDIDATES:
        if os.path.isabs(c) and os.path.exists(c):
            return c
        found = shutil.which(c)
        if found:
            return found
    sys.exit("Chrome が見つからない。環境変数 CHROME_PATH に実行ファイルの場所を入れる")


def width_of(html_text: str) -> int:
    m = re.search(r"body\{width:(\d+)px", html_text)
    if m:
        return int(m.group(1))
    if "components.css" in html_text:
        return 1760
    if "overview.css" in html_text:
        return 1500
    return 1680


def ensure_css(html_path: Path, html_text: str) -> None:
    for name in re.findall(r"(?:href|src)=([\w./-]+\.(?:css|js))", html_text):
        target = (html_path.parent / name).resolve()
        source = ASSETS / Path(name).name
        if not target.exists() and source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, target)


def trim(png: Path) -> tuple[int, int]:
    im = Image.open(png).convert("RGB")
    w, h = im.size
    bg = im.getpixel((w - 2, h - 2))
    px = im.load()
    last = h - 1
    while last > 0 and all(px[x, last] == bg for x in range(0, w, 4)):
        last -= 1
    if last >= h - MARGIN:
        print(f"注意: {png.name} は下端まで中身がある。TALL を増やして描き直す", file=sys.stderr)
    im = im.crop((0, 0, w, min(h, last + MARGIN)))
    im.save(png)
    return im.size


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    chrome = find_chrome()
    for arg in sys.argv[1:]:
        html_path = Path(arg).resolve()
        text = html_path.read_text(encoding="utf-8")
        ensure_css(html_path, text)
        png = html_path.with_suffix(".png")
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=2", f"--window-size={width_of(text)},{TALL}",
             f"--screenshot={png}", html_path.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        print(png, trim(png))


if __name__ == "__main__":
    main()
