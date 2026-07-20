# -*- coding: utf-8 -*-
"""扫描校对流水线真实状态，生成自包含进度看板 progress.html（内联数据，双击即看，刷新即最新）。"""
import json, os, glob, datetime

BASE = "D:/WorkBuddy/2026-07-19-13-09-19/doc_data"
CORR_IN = os.path.join(BASE, "corr_in")
CORR_OUT = os.path.join(BASE, "corr_out")
SIMP = os.path.join(BASE, "videos_simp.json")
OUT_HTML = "D:/WorkBuddy/2026-07-19-13-09-19/progress.html"

def load(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None

# ---- 1. 逐批扫描 ----
in_files = sorted(glob.glob(os.path.join(CORR_IN, "batch_*.json")))
batches = []
for inf in in_files:
    bn = os.path.basename(inf)
    num = bn.replace("batch_", "").replace(".json", "")
    inv = load(inf)
    in_cnt = len(inv) if inv else 0
    in_lines = sum(len(v.get('lines', [])) for v in inv) if inv else 0
    outf = os.path.join(CORR_OUT, bn)
    status, out_cnt, out_lines, mtime = "待处理", 0, 0, ""
    if os.path.exists(outf):
        outv = load(outf)
        if outv is None:
            status = "异常·解析失败"
        else:
            out_cnt = len(outv)
            out_lines = sum(len(v.get('lines', [])) for v in outv)
            status = "已完成" if (out_cnt == in_cnt and out_lines == in_lines) else "异常·行数不符"
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(outf)).strftime("%m-%d %H:%M")
    batches.append({"num": num, "in_cnt": in_cnt, "in_lines": in_lines,
                    "out_cnt": out_cnt, "out_lines": out_lines, "status": status, "mtime": mtime})

done_n = sum(1 for b in batches if b['status'] == "已完成")
total = len(batches)
done_lines = sum(b['out_lines'] for b in batches if b['status'] == "已完成")
total_lines = sum(b['in_lines'] for b in batches)

# ---- 2. 整体阶段 ----
simp = load(SIMP)
simp_videos = len(simp) if simp else 0
simp_lines = sum(len(v.get('lines', [])) for v in simp) if simp else 0

phases = [
    {"name": "阶段1 · 转写+结构化总册", "state": "done", "desc": "225/225 篇 场景/台词/行为 结构化，HTML总册已生成"},
    {"name": "阶段2 · 系统词典校对", "state": "done", "desc": "台词481处 + 场景/行为250处 同音/形近错字已修正"},
    {"name": "阶段3 · LLM全量精校", "state": "doing" if done_n < total else "done",
     "desc": f"{done_n}/{total} 批完成，{done_lines}/{total_lines} 行已精校"},
    {"name": "阶段4 · 字段增强+去英文后缀", "state": "todo", "desc": "讨论中（语气/情绪等候选字段）；'行为 BEHAVIORS'英文后缀待去除"},
]

data = {
    "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "batches": batches, "done_n": done_n, "total": total,
    "done_lines": done_lines, "total_lines": total_lines,
    "simp_videos": simp_videos, "simp_lines": simp_lines, "phases": phases,
}

# ---- 3. 渲染自包含 HTML ----
rows = ""
for b in batches:
    color = "#2e7d32" if b['status'] == "已完成" else ("#c62828" if b['status'].startswith("异常") else "#888")
    bg = "#e8f5e9" if b['status'] == "已完成" else ("#ffebee" if b['status'].startswith("异常") else "#f5f5f5")
    rows += f"""<tr style="background:{bg}">
      <td>batch_{b['num']}</td><td>{b['in_cnt']}</td><td>{b['out_lines']}/{b['in_lines']}</td>
      <td style="color:{color};font-weight:700">{b['status']}</td><td>{b['mtime']}</td></tr>"""

phase_cards = ""
for p in phases:
    badge = {"done": ("已完成", "#2e7d32", "#e8f5e9"), "doing": ("进行中", "#ef6c00", "#fff3e0"),
             "todo": ("待处理", "#888", "#f5f5f5")}[p['state']]
    phase_cards += f"""<div class="card">
      <div class="badge" style="background:{badge[2]};color:{badge[1]}">{badge[0]}</div>
      <div class="pname">{p['name']}</div>
      <div class="pdesc">{p['desc']}</div></div>"""

pct = int(done_lines / total_lines * 100) if total_lines else 0
html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>校对进度看板 · mrlovewords9272</title>
<style>
*{{box-sizing:border-box}} body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;background:#fafafa;color:#222;padding:24px}}
h1{{font-size:22px;margin:0 0 4px}} .meta{{color:#888;font-size:13px;margin-bottom:20px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-bottom:24px}}
.card{{background:#fff;border:1px solid #eee;border-radius:10px;padding:14px;position:relative}}
.badge{{display:inline-block;font-size:12px;padding:2px 8px;border-radius:20px;margin-bottom:8px}}
.pname{{font-weight:700;font-size:15px;margin-bottom:6px}} .pdesc{{font-size:13px;color:#666;line-height:1.5}}
.barwrap{{background:#fff;border:1px solid #eee;border-radius:10px;padding:16px;margin-bottom:24px}}
.bartop{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}}
.bartop b{{font-size:16px}} .bar{{height:14px;background:#eee;border-radius:8px;overflow:hidden}}
.fill{{height:100%;background:linear-gradient(90deg,#ef6c00,#2e7d32);width:{pct}%}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #eee;border-radius:10px;overflow:hidden}}
th,td{{padding:10px 12px;text-align:left;font-size:13px;border-bottom:1px solid #f0f0f0}}
th{{background:#fafafa;color:#555;font-weight:600}}
tr:last-child td{{border-bottom:none}}
.foot{{color:#aaa;font-size:12px;margin-top:16px}}
</style></head><body>
<h1>📊 错别字校对进度看板</h1>
<div class="meta">项目：mrlovewords9272 频道 · 225篇 / 280视频 · 最后更新：{data['generated']}</div>

<div class="cards">{phase_cards}</div>

<div class="barwrap">
  <div class="bartop"><b>LLM 全量精校进度</b><span>{done_n}/{total} 批 · {done_lines}/{total_lines} 行 ({pct}%)</span></div>
  <div class="bar"><div class="fill"></div></div>
</div>

<table><thead><tr><th>批次</th><th>篇数</th><th>已精校行/总行</th><th>状态</th><th>完成时间</th></tr></thead>
<tbody>{rows}</tbody></table>

<div class="foot">数据由 gen_progress.py 实时扫描 doc_data/corr_in、corr_out、videos_simp.json 生成。每次推进后重跑脚本即可刷新本页。</div>
</body></html>"""

open(OUT_HTML, "w", encoding="utf-8").write(html)
print("progress.html 已生成 ->", OUT_HTML)
print(f"LLM精校: {done_n}/{total} 批完成, {done_lines}/{total_lines} 行 ({pct}%)")
print("各批状态:", {b['num']: b['status'] for b in batches})
