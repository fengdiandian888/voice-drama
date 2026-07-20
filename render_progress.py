# -*- coding: utf-8 -*-
"""读 progress_status.json -> 渲染状态灯进度页 progress.html"""
import json, os

BASE = r"D:\WorkBuddy\2026-07-19-13-09-19"
DATA = os.path.join(BASE, "doc_data")
S = json.load(open(os.path.join(DATA, "progress_status.json"), encoding="utf-8"))

done = sum(1 for c in S["chunks"] if c["status"] == "完成")
fail = sum(1 for c in S["chunks"] if c["status"] == "失败")
run  = sum(1 for c in S["chunks"] if c["status"] == "进行中")
wait = sum(1 for c in S["chunks"] if c["status"] == "待处理")
pct = int(done / S["total_chunks"] * 100) if S["total_chunks"] else 0

COLOR = {"待处理":"#d9d9d9","进行中":"#1890ff","完成":"#52c41a","失败":"#ff4d4f"}

cells = []
for c in S["chunks"]:
    col = COLOR.get(c["status"], "#d9d9d9")
    tip = " | ".join(c["titles"]) if c["titles"] else ""
    note = f'<div class="note">{c["note"]}</div>' if c["note"] else ""
    cells.append(
        f'<div class="cell" style="background:{col}" title="{tip}">'
        f'<span class="num">{c["idx"]:02d}</span>{note}</div>')

fail_notes = "".join(
    f'<li><b>块 {c["idx"]:02d}</b>：{c["note"]}（{" / ".join(c["ids"])}）</li>'
    for c in S["chunks"] if c["status"] == "失败")

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>总册调整进度看板</title>
<style>
*{{box-sizing:border-box}}
body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;margin:0;background:#f5f6f8;color:#222;padding:20px}}
h1{{font-size:20px;margin:0 0 4px}}
.sub{{color:#888;font-size:13px;margin-bottom:16px}}
.cards{{display:flex;gap:12px;margin-bottom:18px;flex-wrap:wrap}}
.card{{background:#fff;border-radius:10px;padding:12px 18px;box-shadow:0 1px 3px rgba(0,0,0,.08);min-width:90px}}
.card .n{{font-size:24px;font-weight:700}}
.card .l{{font-size:12px;color:#888}}
.bar{{height:14px;background:#e9e9e9;border-radius:7px;overflow:hidden;margin:6px 0 18px}}
.bar>i{{display:block;height:100%;background:linear-gradient(90deg,#52c41a,#73d13d);width:{pct}%}}
.grid{{display:grid;grid-template-columns:repeat(15,1fr);gap:6px}}
.cell{{border-radius:6px;height:38px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;position:relative;cursor:default}}
.cell .num{{font-weight:700}}
.note{{position:absolute;bottom:1px;font-size:8px;opacity:.9}}
.fails{{background:#fff;border-radius:10px;padding:14px 18px;margin-top:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.fails h3{{margin:0 0 8px;font-size:15px;color:#ff4d4f}}
.fails li{{font-size:13px;margin:4px 0;color:#555}}
.spec{{background:#fff;border-radius:10px;padding:14px 18px;margin-top:18px;box-shadow:0 1px 3px rgba(0,0,0,.08);font-size:13px;line-height:1.7}}
.spec h3{{margin:0 0 8px;font-size:15px}}
.spec code{{background:#f0f0f0;padding:1px 5px;border-radius:4px}}
.legend{{display:flex;gap:14px;font-size:12px;color:#666;margin-bottom:10px}}
.legend i{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:4px;vertical-align:-1px}}
</style></head>
<body>
<h1>总册一次性调整 · 进度看板</h1>
<div class="sub">最后更新：{S['updated_at']} ｜ 共 {S['total']} 篇 / {S['total_chunks']} 块（5篇/块）｜ 错别字LLM已完成 {S['typo_llm_batches']}/15 批</div>

<div class="cards">
  <div class="card"><div class="n" style="color:#52c41a">{done}</div><div class="l">已完成</div></div>
  <div class="card"><div class="n" style="color:#1890ff">{run}</div><div class="l">进行中</div></div>
  <div class="card"><div class="n" style="color:#ff4d4f">{fail}</div><div class="l">失败</div></div>
  <div class="card"><div class="n" style="color:#999">{wait}</div><div class="l">待处理</div></div>
</div>
<div class="bar"><i></i></div>

<div class="legend">
  <span><i style="background:#52c41a"></i>完成</span>
  <span><i style="background:#1890ff"></i>进行中</span>
  <span><i style="background:#ff4d4f"></i>失败</span>
  <span><i style="background:#d9d9d9"></i>待处理</span>
</div>
<div class="grid">{''.join(cells)}</div>

<div class="fails"><h3>卡点说明（失败块）</h3>
{fail_notes if fail_notes else '<div style="font-size:13px;color:#999">暂无</div>'}
</div>

<div class="spec">
<h3>已锁定的一次性调整规格</h3>
<b>① 错别字校对</b>：全 225 篇逐行（同音/形近/漏字），已 LLM 7/15 批。<br>
<b>② 字段增强</b>（逐行）：说话人(文中称呼) / 语气<code>[标签]</code> / 音效<code>[标签]</code>；（篇级）语气总结 / 题材标签 / 情感弧线 / 强度 / 听者角色 / 标志性元素。英文后缀全去掉。<br>
<b>③ 文本调整</b>：标题<code>中文(English)</code> ｜ 角色用文中称呼 ｜ 口语冗余保留原貌 ｜ 敏感标<code>[敏感]</code>可筛选 ｜ 英文词回正 ｜ 场景行为描述统一 ｜ 纯语气词归音效。<br>
<b>执行</b>：5 篇/块串行，每块落盘后更新本页；卡住只重跑当前块。55 年龄墙篇待本机 <code>download_age.bat</code>。
</div>
</body></html>"""

open(os.path.join(BASE, "progress.html"), "w", encoding="utf-8").write(HTML)
print("progress.html rendered | done=%d run=%d fail=%d wait=%d" % (done, run, fail, wait))
