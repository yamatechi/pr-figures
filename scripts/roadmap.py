#!/usr/bin/env python3
"""PR の全体像の図（HTML）を、JSON の定義から PR ごとに作る。

使い方:
  python3 roadmap.py <roadmap.json> <出力ディレクトリ>
    → <出力ディレクトリ>/roadmap-<番号>.html を、JSON の current に並べた PR ごとに 1 枚ずつ書く

JSON の形:
{
  "title": "写真の公開前チェックの PR の全体像",
  "subtitle": "サムネイルと判定を通ったものだけを公開する。左から順に入れる",
  "current": ["#212", "#88"],          // この PR として強調する番号。1 つにつき 1 枚
  "lanes": [
    {"name": "バックエンド", "items": [
      {"num": "#211", "title": "投稿に状態の列を足す", "status": "merged"},
      {"num": "次", "title": "写真の判定と公開", "status": "next", "note": "前提: #213"}
    ]},
    {"name": "アプリ", "items": [
      {"num": "#88", "title": "処理中の投稿を本人にだけ出す", "status": "open"}
    ]}
  ],
  "timeline": [
    {"text": "ステージングで通しの確認"},
    {"text": "v2.3.0 リリース", "emphasis": true}
  ]}
status は merged（merge 済み）・open（レビュー中）・next（これから）のどれか。
"""
import html
import json
import shutil
import sys
from pathlib import Path

LABEL = {"merged": "merge 済み", "open": "レビュー中", "next": "これから"}

STYLE = """
body{width:1680px}
.lane{display:grid;grid-template-columns:132px minmax(0,1fr);gap:12px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px}
.ln{font-weight:700;font-size:16px;color:var(--muted);white-space:nowrap}
.row{display:flex;align-items:stretch;gap:6px;min-width:0}
.arr{align-self:center;color:var(--todo);font-size:18px}
.card{flex:1 1 0;min-width:0;border-radius:9px;padding:10px 11px;display:flex;flex-direction:column;gap:6px;border:1.5px solid var(--line);background:var(--card)}
.card.pad{visibility:hidden}
.card.merged{background:var(--ok-s);border-color:#9fd2b5}
.card.open{background:var(--warn-s);border-color:#e7c27f}
.card.next{border-style:dashed;border-color:#b9bfca}
.card.me{background:var(--acc-s);border:3px solid var(--acc);box-shadow:0 0 0 4px #c9d6fb}
.top{display:flex;justify-content:space-between;align-items:center}
.num{font-family:"SF Mono",Menlo,monospace;font-weight:600;font-size:15px}
.st{font-size:12px;font-weight:600}
.merged .st{color:var(--ok)} .open .st{color:var(--warn)} .next .st{color:var(--todo)}
.this{font-size:12px;color:#fff;background:var(--acc);padding:2px 8px;border-radius:999px}
.t{font-size:13.5px;line-height:1.5}
.pre{display:block;margin-top:4px;font-size:12px;color:var(--muted)}
.tl{display:flex;align-items:center;gap:10px;font-size:15px;flex-wrap:wrap}
.tl div{background:#fff;border:1px solid var(--line);border-radius:999px;padding:8px 16px}
.tl .em{border-color:var(--warn);color:var(--warn);font-weight:700}
.tl .sub{display:block;font-size:13px;color:var(--muted);font-weight:400}
"""


def esc(s):
    return html.escape(s or "")


def card(item, current):
    if item.get("status") == "pad":
        return "<div class='card pad'></div>"
    status = item["status"]
    me = item["num"] == current
    tag = "<b class='this'>この PR</b>" if me else f"<b class='st'>{LABEL[status]}</b>"
    note = f"<span class='pre'>{esc(item.get('note'))}</span>" if item.get("note") else ""
    cls = status + (" me" if me else "")
    return (f"<div class='card {cls}'><div class='top'><span class='num'>{esc(item['num'])}</span>{tag}</div>"
            f"<div class='t'>{esc(item['title'])}{note}</div></div>")


def lane(spec, width, current):
    items = list(spec["items"]) + [{"status": "pad"}] * (width - len(spec["items"]))
    parts = []
    for i, item in enumerate(items):
        if i > 0:
            hidden = " style='visibility:hidden'" if item.get("status") == "pad" else ""
            parts.append(f"<span class='arr'{hidden}>→</span>")
        parts.append(card(item, current))
    return f"<div class='lane'><div class='ln'>{esc(spec['name'])}</div><div class='row'>{''.join(parts)}</div></div>"


def timeline(steps):
    chips = []
    for s in steps:
        sub = f"<span class='sub'>{esc(s.get('sub'))}</span>" if s.get("sub") else ""
        cls = " class='em'" if s.get("emphasis") else ""
        chips.append(f"<div{cls}>{esc(s['text'])}{sub}</div>")
    return "<div class=tl>" + "<span class=arr>→</span>".join(chips) + "</div>" if chips else ""


def build(spec, current):
    width = max(len(l["items"]) for l in spec["lanes"])  # 全レーンのカードの幅をそろえる
    legend = ('<div class=legend><span><i style="background:var(--ok-s);border:1px solid #9fd2b5"></i>merge 済み</span>'
              '<span><i style="background:var(--warn-s);border:1px solid #e7c27f"></i>レビュー中</span>'
              '<span><i style="border:1.5px dashed #b9bfca"></i>これから</span>'
              '<span><i style="background:var(--acc-s);border:2px solid var(--acc)"></i>この PR</span></div>')
    return (f"<!doctype html><meta charset=utf-8><link rel=stylesheet href=common.css><style>{STYLE}</style>"
            f"<div class=page><div><h1>{esc(spec['title'])}</h1><div class=sub>{esc(spec.get('subtitle'))}</div></div>"
            f"{legend}{''.join(lane(l, width, current) for l in spec['lanes'])}{timeline(spec.get('timeline', []))}</div>")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).resolve().parent.parent / "assets" / "common.css", out / "common.css")
    for current in spec["current"]:
        path = out / f"roadmap-{current.lstrip('#')}.html"
        path.write_text(build(spec, current), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
