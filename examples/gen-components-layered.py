#!/usr/bin/env python3
"""層 × 担当する側の構成図を、1 つの部品の表から PR ごとに 1 枚ずつ書く例（架空の「料理教室の予約」）。

部品ごとに「既定の状態・作る PR・置く行と列」を表にし、PR ごとに .me の色だけ変えて書き出す。
写して使うときは PRS・B・LAYERS・ARROWS・列の見出しと grid-template-columns を書き換える。

横の帯が層（画面・入口・処理・DB）、縦の列が担当する側（会員・予約の基盤・教室の運営者）。

python3 gen-components-layered.py <出力フォルダ> [assets への相対パス]
  → <出力フォルダ>/components-<番号>.html（assets への相対パスの既定は assets/）
"""
import sys
from pathlib import Path

PRS = ["51", "52", "53", "54", "55", "56"]

# グリッドの列: 1 層の名前 / 2-3 会員 / 4 区切り / 5-7 予約の基盤 / 8 区切り / 9-11 教室の運営者
# id: (既定の状態, この部品を作る・手を入れる PR, 名前, 識別子, 説明, 行, 列)
B = {
    # 画面
    "mypage": ("", [], "マイページ", "pages/me/bookings", "自分の予約を見る・取り消す", 2, "2"),
    "book": ("new", ["54"], "予約の画面", "pages/classes/[id]/book", "空いている回を選んで予約する", 2, "3"),
    "slotui": ("", [], "開講日の管理画面", "admin/schedules", "開講日と定員を登録する", 2, "10"),
    "roster": ("new", ["56"], "出席者の名簿", "admin/rosters", "当日の予約者を一覧で見る", 2, "11"),
    # 入口（API・定期実行）
    "myapi": ("mod", ["53"], "自分の予約の API", "GET /v1/me/bookings", "取り消し済みも区別して返す", 3, "2"),
    "bookapi": ("new", ["52"], "予約の API", "POST /v1/bookings", "空きを確かめて予約を作る", 3, "3"),
    "cron": ("new", ["55"], "前日のリマインド", "send-reminders", "18 時に翌日の予約者を積む", 3, "7"),
    "slotapi": ("mod", ["51"], "開講日の API", "PUT /v1/admin/slots/{id}", "定員を予約数より下げられない", 3, "10"),
    "rosterapi": ("new", ["56"], "名簿の API", "GET /v1/admin/slots/{id}/roster", "回ごとの予約者を返す", 3, "11"),
    # 処理（worker・ドメイン）
    "capacity": ("new", ["52"], "空きの判定", "SlotCapacityPolicy", "定員と予約数を比べる", 4, "5"),
    "queue": ("new", ["52"], "通知のキュー", "notification-jobs", "送るメールを順に並べる", 4, "6"),
    "worker": ("new", ["52"], "通知のワーカー", "NotificationWorker", "メールを送り、履歴に書く", 4, "7"),
    # DB・送り先
    "bookings": ("mod", ["51", "52"], "予約の表", "booking", "会員・回・状態（予約中・取り消し）", 5, "2 / 4"),
    "history": ("new", ["52"], "通知の履歴", "notification_log", "同じ通知を二度送らない", 5, "6"),
    "mail": ("", [], "メール配信（外部）", "", "確認とリマインドのメール", 5, "7"),
    "slots": ("mod", ["51"], "開講日の表", "class_slot", "日時・定員", 5, "10 / 12"),
}

LAYERS = [(2, "画面", "frontend"), (3, "入口", "API・定期実行"), (4, "処理", "worker・ドメイン"), (5, "DB", "送り先")]

ARROWS = """
 ['mypage','myapi','b','t',''],
 ['book','bookapi','b','t',''],
 ['slotui','slotapi','b','t',''],
 ['roster','rosterapi','b','t',''],
 ['myapi','bookings','b','tl','読む'],
 ['bookapi','capacity','r','t','空きを聞く',0.3,'above'],
 ['capacity','bookings','b','r','予約を書く',0.6,'left'],
 ['capacity','queue','r','l',''],
 ['cron','queue','b','t','積む',0.5,'left'],
 ['queue','worker','r','l',''],
 ['worker','mail','b','t','送る'],
 ['worker','history','b','r','書く',0.5,'left'],
 ['slotapi','slots','b','tl','書く'],
 ['rosterapi','slots','b','tr','読む'],
"""

def box(i: str, pr: str) -> str:
    state, prs, n, m, d, row, col = B[i]
    if pr in prs:
        cls, tag = "c me", f'<span class="tag me">#{pr}</span>'
    elif state == "new":
        cls, tag = "c new", f'<span class=tag>{"次" if not prs else "新"}</span>'
    elif state == "mod":
        cls, tag = "c mod", "<span class=tag>手を入れる</span>"
    else:
        cls, tag = "c", ""
    mm = f"<div class=m>{m}</div>" if m else ""
    return (f'<div class="{cls}" id={i} style="grid-row:{row};grid-column:{col}">'
            f'{tag}<div class=n>{n}</div>{mm}<div class=d>{d}</div></div>')


def page(pr: str, assets: str) -> str:
    bands = "\n".join(
        f'<div class="band{" alt" if k % 2 else ""}" style="grid-row:{r}"></div>'
        f'<div class=ll style="grid-row:{r}"><b>{name}</b><span>{sub}</span></div>'
        for k, (r, name, sub) in enumerate(LAYERS))
    boxes = "\n".join(box(i, pr) for i in B)
    return f"""<!doctype html><meta charset=utf-8><link rel=stylesheet href={assets}common.css><link rel=stylesheet href={assets}overview.css><link rel=stylesheet href={assets}components.css>
<style>
body{{width:2210px}}
.c .m{{overflow-wrap:normal;word-break:normal}}
.grid{{grid-template-columns:116px 210px 210px 26px 210px 210px 210px 26px 210px 210px 210px 8px;column-gap:22px;row-gap:14px;align-items:center}}
.band{{grid-column:1 / -1;align-self:stretch;background:#eceff4;border-radius:12px}}
.band.alt{{background:#f4f6f9}}
.ll{{grid-column:1;padding-left:16px;display:flex;flex-direction:column;gap:2px}}
.ll b{{font-size:17px}}
.ll span{{font-size:11.5px;white-space:nowrap;color:var(--muted)}}
.c{{margin:20px 0}}
.colh{{grid-row:1;text-align:center;font-weight:700;font-size:16px;padding:4px 0;border-bottom:3px solid #b9bfca}}
.colh span{{display:block;font-weight:400;font-size:12.5px;color:var(--muted)}}
.sep{{grid-row:2 / 6;align-self:stretch;justify-self:center;border-left:2px dashed #c3c8d2}}
</style>
<div class=page>
<div><h1>料理教室の予約とリマインドの仕組み（予定：後続の PR がすべて入ったあと）</h1><div class=sub>会員の予約は空きを確かめてから作り、確認と前日のリマインドのメールは基盤のキューから送る。運営者は開講日と名簿を扱う</div></div>
<div class=legend><span><i style="background:var(--ok-s);border-color:#9fd2b5"></i>新しく作る（ほかの PR）</span><span><i style="background:var(--acc-s);border:2px solid var(--acc)"></i>この PR（#{pr}）で作る・手を入れる</span><span><i style="background:#fff"></i>手を入れる（ほかの PR）</span><span><i style="background:#f6f7f9"></i>今のまま</span></div>
<div id=wrap>
<svg id=arrows></svg>
<div class=grid>
<div class=colh style="grid-column:2 / 4">会員<span>予約する</span></div>
<div class=colh style="grid-column:5 / 8">予約の基盤<span>空きの判定と通知</span></div>
<div class=colh style="grid-column:9 / 12">教室の運営者<span>開講日を決める・名簿を見る</span></div>
{bands}
<div class=sep style="grid-column:4"></div>
<div class=sep style="grid-column:8"></div>
{boxes}
</div></div>
</div>
<script>
window.ARROWS=[{ARROWS}];
</script>
<script src={assets}arrows.js></script>
"""


if __name__ == "__main__":
    here = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    assets = sys.argv[2] if len(sys.argv) > 2 else "assets/"
    here.mkdir(parents=True, exist_ok=True)
    for pr in PRS:
        (here / f"components-{pr}.html").write_text(page(pr, assets), encoding="utf-8")
    print("ok", len(PRS))
