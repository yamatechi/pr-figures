// 構成図の矢印を、描いた箱の位置から SVG で引く。
// HTML 側で window.ARROWS を定義してから読む:
//   [from の id, to の id, from の辺, to の辺, ラベル, ラベルの位置(0〜1、既定 0.5), ラベルの置き方('right'|'left'|'above'、既定 'right')]
//   辺は t・b・l・r と、上辺の右寄り tr・左寄り tl（同じ箱の上辺に 2 本入るとき）
// 識別子（.m）は - / _ の後と、クラス名の語の切れ目（小文字の後の大文字の前）でだけ折り返すよう <wbr> を入れる。
// URL のクエリ（? や = を含む語）は語の切れ目で折らない（includeArchived が include / Archived に割れるため）
(function () {
  document.querySelectorAll('.m').forEach((e) => {
    e.innerHTML = e.innerHTML
      .split(' ')
      .map((w) => (/[?=]/.test(w) ? w : w.replace(/(?<=[a-z])(?=[A-Z])/g, '<wbr>')))
      .join(' ')
      .replace(/([-\/_])/g, '$1<wbr>');
  });
  const wrap = document.getElementById('wrap');
  const svg = document.getElementById('arrows');
  svg.setAttribute('width', wrap.offsetWidth);
  svg.setAttribute('height', wrap.offsetHeight);
  svg.innerHTML =
    '<defs><marker id=h viewBox="0 0 10 10" refX=9 refY=5 markerWidth=7 markerHeight=7 orient=auto-start-reverse><path d="M0,0L10,5L0,10z" fill="#7a8190"/></marker></defs>';
  const wr = wrap.getBoundingClientRect();
  const NS = 'http://www.w3.org/2000/svg';
  function pt(id, s) {
    const el = document.getElementById(id);
    if (!el) throw new Error('arrows.js: id が無い: ' + id);
    const r = el.getBoundingClientRect();
    const x = r.left - wr.left, y = r.top - wr.top;
    return {
      t: [x + r.width / 2, y], tl: [x + r.width * 0.2, y], tr: [x + r.width * 0.8, y],
      b: [x + r.width / 2, y + r.height], l: [x, y + r.height / 2], r: [x + r.width, y + r.height / 2],
    }[s];
  }
  const dir = { t: [0, -1], tl: [0, -1], tr: [0, -1], b: [0, 1], l: [-1, 0], r: [1, 0] };
  for (const [f, t, fs, ts, label, pos = 0.5, side = 'right'] of window.ARROWS || []) {
    const p = pt(f, fs), q = pt(t, ts);
    const k = Math.max(30, Math.min(140, Math.hypot(q[0] - p[0], q[1] - p[1]) / 2.5));
    const c1 = [p[0] + dir[fs][0] * k, p[1] + dir[fs][1] * k];
    const c2 = [q[0] + dir[ts][0] * k, q[1] + dir[ts][1] * k];
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', `M${p}C${c1} ${c2} ${q}`);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', '#7a8190');
    path.setAttribute('stroke-width', '1.8');
    path.setAttribute('marker-end', 'url(#h)');
    svg.appendChild(path);
    if (!label) continue;
    const m = path.getPointAtLength(path.getTotalLength() * pos);
    const off = { right: [6, 4], left: [-6, 4], above: [-10, -10] }[side];
    const tx = document.createElementNS(NS, 'text');
    tx.setAttribute('x', m.x + off[0]);
    tx.setAttribute('y', m.y + off[1]);
    if (side !== 'right') tx.setAttribute('text-anchor', 'end');
    tx.setAttribute('class', 'lbl');
    tx.textContent = label;
    svg.appendChild(tx);
  }
})();
