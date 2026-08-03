#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the Lの系列音声剧 225-篇 Structured Catalog (同步增强版).

数据源:
  - doc_data/videos_simp.json   (225篇基础台词, 已系统错别字校对)
  - doc_data/behavior_simp.json (场景 + 行为节点)
  - doc_data/enriched/chunk_*.json (已完成"一次性调整"的篇: 说话人/语气/音效/篇级分析)
合并规则: 每篇默认用基础数据; 若 enriched 中存在同 id, 则叠加新字段并标记 enriched.

交互功能 (v2 重写: 封面网格 → 详情 两层结构):
  - 封面网格浏览（YouTube 缩略图），点开单篇看完整台词（剧本视图）
  - 说话人身份层级配色: 上位者=蓝 / 下位者=粉 / 其他=灰 / 未识别(统称"他")=虚线灰
  - 语气态度配色: 左侧色条仅在非平静语气上色
  - 手动纠错 v2: localStorage 覆盖，升级自 v1（旧 v1 自动清除）
"""
import json, os, glob

# 题材标签归一：把碎片标签合并为稳定大类（用于分组与总览）
GENRE_MAP = {
    "主仆/调教": ["主仆/调教","主仆","调教","BDSM","权力关系","权力","掌控","服从","训诫","惩罚","质问"],
    "现代情侣": ["现代情侣","现代","情侣","夫妻","日常甜宠","日常关怀","日常","调情","吃醋","信任","晚归","和好","出走与挽留","分离焦虑","情书","独白","占有"],
    "校园": ["校园/师生","校园","师生"],
    "古风": ["古风"],
    "治愈/宠溺": ["治愈","宠溺","安抚","安慰","情绪安抚","心疼","自伤关怀","管教后安抚","睡前"],
    "家庭/长辈": ["家庭/长辈","家庭"],
    "职场": ["职场","金主"],
    "医疗": ["医疗"],
    "宠物扮演": ["宠物扮演"],
}
TAG2MAIN = {}
for _main, _tags in GENRE_MAP.items():
    for _t in _tags:
        TAG2MAIN[_t] = _main

def genre_main(tags):
    for t in (tags or []):
        if t in TAG2MAIN:
            return TAG2MAIN[t]
    return "其他"

BASE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(BASE, "doc_data")

vids = json.load(open(os.path.join(DOC, "videos_simp.json"), encoding="utf-8"))
beh = json.load(open(os.path.join(DOC, "behavior_simp.json"), encoding="utf-8"))

# 加载所有已完成富集块
enriched_index = {}
for f in sorted(glob.glob(os.path.join(DOC, "enriched", "chunk_*.json"))):
    for o in json.load(open(f, encoding="utf-8")):
        enriched_index[o["id"]] = o

TOTAL_CHANNEL = 280   # 全频道视频数
DONE_TRANSCRIBE = len(vids)  # 225 已转写

records = []
for i, x in enumerate(vids, 1):
    vid = x["id"]
    b = beh.get(vid, {})
    e = enriched_index.get(vid)
    if e:
        lines = [{"ts": l.get("ts", ""), "text": l.get("text", ""),
                  "speaker": l.get("speaker", ""), "tone": l.get("tone", ""),
                  "sound": l.get("sound", [])} for l in e.get("lines", [])]
        scene = e.get("scene", "") or b.get("scene", "")
        ebeh = e.get("behaviors", []) or b.get("behaviors", [])
        behaviors = [{"desc": bb.get("desc", "")} for bb in ebeh]
        rec = {
            "no": i, "id": vid,
            "title": e.get("title", x.get("title", "")),
            "title_zh": e.get("title_zh", ""),
            "duration": e.get("duration", x.get("duration", "")),
            "link": e.get("link", x.get("link", "")),
            "enriched": True,
            "lines": lines, "scene": scene, "behaviors": behaviors,
            "tone_summary": e.get("tone_summary", ""),
            "genre_tags": e.get("genre_tags", []),
            "genre_main": genre_main(e.get("genre_tags", [])),
            "emotion_arc": e.get("emotion_arc", ""),
            "intensity": e.get("intensity", ""),
            "listener_role": e.get("listener_role", ""),
            "signature_elements": e.get("signature_elements", []),
            "sensitive": bool(e.get("sensitive", False)),
            "tier": e.get("tier", "hand"),
            "story": e.get("story", []),
        }
    else:
        lines = [{"ts": l[0], "text": l[1], "speaker": "", "tone": "", "sound": []}
                 for l in x.get("lines", [])]
        scene = b.get("scene", "")
        behaviors = [{"desc": bb.get("desc", bb.get("ts", ""))} for bb in b.get("behaviors", [])]
        rec = {
            "no": i, "id": vid,
            "title": x.get("title", ""), "title_zh": "",
            "duration": x.get("duration", ""), "link": x.get("link", ""),
            "enriched": False,
            "lines": lines, "scene": scene, "behaviors": behaviors,
            "tone_summary": "", "genre_tags": [], "emotion_arc": "",
            "intensity": "", "listener_role": "", "signature_elements": [],
            "sensitive": False, "tier": "",
        }
    records.append(rec)

# 加载额外已转写视频（年龄墙补齐等），存在则追加到末尾
extra_path = os.path.join(DOC, "extra_videos.json")
if os.path.exists(extra_path):
    try:
        extras = json.load(open(extra_path, encoding="utf-8"))
        for j, x in enumerate(extras, 1):
            rec = {
                "no": len(records) + j, "id": x["id"],
                "title": x.get("title", x["id"]), "title_zh": x.get("title_zh", x.get("title", x["id"])),
                "duration": x.get("duration", ""), "link": x.get("link", ""),
                "enriched": bool(x.get("enriched", True)),
                "lines": x.get("lines", []),
                "scene": x.get("scene", ""),
                "behaviors": x.get("behaviors", []),
                "tone_summary": x.get("tone_summary", ""),
                "genre_tags": x.get("genre_tags", []),
                "genre_main": genre_main(x.get("genre_tags", [])),
                "emotion_arc": x.get("emotion_arc", ""),
                "intensity": x.get("intensity", ""),
                "listener_role": x.get("listener_role", ""),
                "signature_elements": x.get("signature_elements", []),
                "sensitive": bool(x.get("sensitive", False)),
                "tier": x.get("tier", "auto"),
            }
            records.append(rec)
        print("extra videos appended:", len(extras))
    except Exception as ex:
        print("extra_videos load error:", ex)

data_json = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
enriched_count = sum(1 for r in records if r["enriched"])
line_count = sum(len(r["lines"]) for r in records)
behavior_count = sum(len(r["behaviors"]) for r in records)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lの女性向音声剧 · Structured Catalog</title>
<style>
  :root{
    --bg:#eef2f6; --panel:#ffffff; --ink:#1f2937; --sub:#64748b;
    --line:#e4e9f0; --accent:#0e7490; --accent2:#0891b2;
    --accent-soft:#ecfeff; --accent-ink:#155e75;
    --tag:#e8f3f6; --barbg:#e4e9f0; --ok:#0d9488;
    --sup:#2563eb; --pink:#db2777; --other:#475569; --unknown:#94a3b8;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
       background:var(--bg);color:var(--ink);font-size:14px;line-height:1.6}
  a{color:inherit;text-decoration:none}
  header{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);
         border-bottom:1px solid var(--line);padding:10px 18px}
  .topbar{display:flex;align-items:center;gap:12px}
  .brand{font-size:16px;font-weight:800;white-space:nowrap;color:var(--accent-ink);letter-spacing:.02em}
  .brand .dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--accent);margin-right:7px;vertical-align:middle}
  .search{flex:1;min-width:0;padding:9px 14px;border:1px solid var(--line);border-radius:10px;font-size:15px;outline:none;background:#f8fafc}
  .search:focus{border-color:var(--accent);background:#fff}
  .hbtns{display:flex;gap:8px;align-items:center}
  .hbtn{cursor:pointer;border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:9px;padding:7px 13px;font-size:13px;font-weight:700;white-space:nowrap}
  .hbtn:hover{border-color:var(--accent);color:var(--accent-ink)}
  .hbtn.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .readbtns{display:inline-flex;gap:3px}
  .readbtns button{border:1px solid var(--line);background:#fff;color:var(--sub);border-radius:7px;padding:5px 9px;font-size:12px;font-weight:600;cursor:pointer}
  .readbtns button.on{background:var(--accent-ink);color:#fff;border-color:var(--accent-ink)}
  .filters{display:flex;gap:10px;margin-top:10px;overflow-x:auto;padding-bottom:4px;-webkit-overflow-scrolling:touch;align-items:center}
  .fgrp{display:flex;align-items:center;gap:6px;font-size:12px;color:#64748b;flex:0 0 auto}
  .fgrp>b{color:#475569;margin-right:2px;font-weight:700}
  .chip{cursor:pointer;padding:4px 12px;border-radius:999px;border:1px solid var(--line);background:#fff;color:#475569;font-size:12.5px;font-weight:600;white-space:nowrap;user-select:none;transition:.12s}
  .chip:hover{border-color:var(--accent);color:var(--accent-ink)}
  .chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .legend{font-size:11px;color:var(--sub);display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-left:auto}
  .legend .it{display:flex;align-items:center;gap:4px}
  .legend .sw{width:11px;height:11px;border-radius:3px;display:inline-block}
  .stats{font-size:12px;color:var(--sub);padding:6px 18px;background:var(--panel);border-bottom:1px solid var(--line)}
  .stats b{color:var(--ink)}
  /* dashboard */
  .dash{display:none;background:var(--panel);border-bottom:1px solid var(--line);padding:14px 20px}
  .dash.open{display:block}
  .dashcols{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px;max-width:1280px;margin:0 auto}
  .dashh{font-size:12px;font-weight:700;color:var(--accent-ink);margin-bottom:6px;letter-spacing:.04em}
  .dashtags{display:flex;flex-wrap:wrap;gap:6px;align-items:flex-start}
  .dtag,.dspk{cursor:pointer;border:1px solid var(--line);background:#fff;color:#475569;border-radius:999px;padding:3px 10px;font-size:12px;line-height:1.5}
  .dtag:hover,.dspk:hover{border-color:var(--accent);color:var(--accent-ink)}
  .dtag.on,.dspk.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .resetbtn{cursor:pointer;border:none;background:none;color:var(--sub);font-size:12px;text-decoration:underline;padding:0 4px}
  .wrap{max-width:1280px;margin:0 auto;padding:18px}
  .gridbar{display:flex;align-items:center;justify-content:space-between;margin:4px 2px 14px;flex-wrap:wrap;gap:8px}
  .cnt{font-size:13px;color:var(--sub)}
  .cnt b{color:var(--ink);font-weight:700}
  .sortbtns{display:flex;gap:6px}
  .sortbtns button{border:1px solid var(--line);background:#fff;border-radius:14px;padding:4px 12px;font-size:12px;font-weight:600;color:#475569;cursor:pointer}
  .sortbtns button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:16px}
  .gcard{background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:.15s;box-shadow:0 1px 3px rgba(15,23,42,.05)}
  .gcard:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(15,23,42,.1);border-color:#cfe6ea}
  .thumb{position:relative;aspect-ratio:16/9;background:linear-gradient(135deg,#e2eef2,#cfe3ea);overflow:hidden}
  .thumb img{width:100%;height:100%;object-fit:cover;display:block}
  .thumb .tf{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:34px;font-weight:800;color:#fff;background:linear-gradient(135deg,var(--accent),var(--accent2))}
  .gcard-body{padding:10px 12px 12px}
  .gtitle{font-size:13.5px;font-weight:700;color:var(--ink);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .gsub{font-size:11px;color:var(--sub);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .gmeta{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-top:8px}
  .gmeta .meta{font-size:11px;color:var(--sub);margin-left:auto}
  .badge{display:inline-block;border-radius:999px;font-size:10.5px;padding:1px 8px;font-weight:600;vertical-align:middle;margin-left:6px}
  .badge.ok{background:#d1fae5;color:#0d9488}
  .badge.auto{background:#fef3c7;color:#b45309}
  .badge.base{background:#f1f5f9;color:#94a3b8}
  .pill{display:inline-block;font-size:11px;border-radius:999px;padding:1px 9px;background:var(--tag);color:var(--accent-ink);border:1px solid #d6ebf0;font-weight:600}
  .pill.warn{background:#fef2f2;color:#b91c1c;border-color:#fecaca}
  .pager{display:flex;align-items:center;justify-content:center;gap:10px;margin:22px 0 10px}
  .pager button{border:1px solid var(--line);background:#fff;border-radius:9px;padding:7px 14px;font-size:13px;font-weight:600;color:#475569;cursor:pointer}
  .pager button:hover:not(:disabled){border-color:var(--accent);color:var(--accent-ink)}
  .pager button:disabled{opacity:.45;cursor:default}
  .pager .pginfo{font-size:13px;color:var(--sub)}
  /* detail */
  #detailView{max-width:860px;margin:0 auto;padding:18px 18px 60px}
  .backbtn{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:9px;padding:7px 14px;font-size:13px;font-weight:700;color:var(--accent-ink);margin-bottom:14px;display:inline-flex;align-items:center;gap:6px}
  .backbtn:hover{border-color:var(--accent)}
  .dtitle{font-size:20px;font-weight:800;color:var(--ink);margin:0 0 4px;line-height:1.4}
  .dsub{font-size:13px;color:var(--sub);margin-bottom:10px}
  .dmetarow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
  .dmetarow a{color:var(--accent);font-weight:600}
  .summary{font-size:13.5px;color:var(--ink);background:#f8fafc;border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-bottom:14px}
  .summary .sep{color:var(--sub);margin:0 5px}
  .transcript{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;max-width:34em}
  /* 台词：分段模式（按说话人归组为段落，而非一句一行） */
  .dpara{position:relative;margin:11px 0;padding:2px 0 2px 13px;border-left:3px solid var(--line)}
  .dpara .spk{display:block;font-size:calc(12px * var(--rs,1));font-weight:700;letter-spacing:.02em;margin-bottom:3px}
  .dpara .diatext{font-size:calc(15.5px * var(--rs,1));line-height:1.95;color:#0f172a;text-align:justify}
  .dpara .dl{display:inline}
  /* 剧本体：叙述 + 彩色台词 */
  .story{font-size:calc(15.5px * var(--rs,1));line-height:2;color:#334155;text-align:justify}
  .story .sn{display:block;margin:10px 0 6px;color:#475569;text-indent:2em}
  .story .sl{margin:5px 0;padding-left:2em;text-indent:-2em}
  .story .sl .spk{display:inline;font-weight:700;margin-right:6px;white-space:nowrap}
  .story .st{font-weight:600}
  .story .snd{color:#94a3b8;font-size:.85em}
  .line-speaker[data-hier="sup"]{color:#2563eb}
  .line-speaker[data-hier="sub"]{color:#db2777}
  .line-speaker[data-hier="other"]{color:#475569}
  .line-speaker[data-hier="unknown"]{color:#94a3b8;background:#f9fafb;border:1px dashed #cbd5e1;border-radius:4px;padding:0 5px}
  .snd{color:#94a3b8;font-size:calc(11px * var(--rs,1));margin-left:5px}
  mark{background:#fde68a;border-radius:2px}
  .empty{color:var(--sub);font-style:italic}
  .meta-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin-top:12px}
  .meta-item{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:8px 10px}
  .meta-item .k{font-size:11px;color:var(--sub);font-weight:600;margin-bottom:2px}
  .meta-item .v{font-size:13px;color:#374151}
  .tag{display:inline-block;background:var(--tag);color:var(--accent-ink);border-radius:6px;font-size:11px;padding:1px 7px;margin:2px 3px 0 0}
  .sensitive{color:#dc2626;font-weight:700}
  .sec{margin-top:14px}
  .sec .t{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:.04em;border-left:3px solid var(--accent);padding-left:8px;margin-bottom:6px}
  ul.beh{list-style:none;margin:0;padding:0}
  ul.beh li{display:flex;gap:10px;padding:5px 0;border-bottom:1px dashed var(--line);font-size:13.5px}
  ul.beh li:last-child{border-bottom:none}
  ul.beh li .num{flex:0 0 30px;color:var(--accent2);font-weight:600}
  .editbtn{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:9px;padding:7px 13px;font-size:13px;font-weight:700;color:var(--ink);white-space:nowrap}
  .editbtn:hover{border-color:var(--accent)}
  .editbtn.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  body.edit .line-speaker,body.edit .dl{cursor:pointer;outline:1px dashed #cbd5e1;outline-offset:2px}
  body.edit .line-speaker:hover,body.edit .dl:hover{filter:brightness(.95)}
  #ovModal{position:fixed;inset:0;background:rgba(15,23,42,.4);display:none;align-items:center;justify-content:center;z-index:300}
  #ovModal .box{background:#fff;border-radius:14px;padding:20px 22px;width:330px;box-shadow:0 12px 40px rgba(0,0,0,.25)}
  #ovModal h3{margin:0 0 4px;font-size:14px}
  #ovModal .sub{font-size:11px;color:var(--sub);margin-bottom:8px}
  #ovModal label{font-size:12px;color:var(--sub);display:block;margin:12px 0 4px;font-weight:600}
  #ovModal input[type=text]{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;font-size:13px;outline:none}
  #ovModal input[type=text]:focus{border-color:var(--accent)}
  #ovModal .rad{display:flex;gap:16px;margin-top:6px}
  #ovModal .rad label{display:flex;align-items:center;gap:5px;margin:0;font-weight:500;color:var(--ink);font-size:13px;cursor:pointer}
  #ovModal .acts{display:flex;gap:8px;justify-content:flex-end;margin-top:18px}
  #ovModal button{cursor:pointer;border:none;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:600}
  #ovModal .save{background:var(--accent);color:#fff}
  #ovModal .cancel{background:#e5e7eb;color:#374151}
  /* ===== 手机端适配（≤780px 严格响应式） ===== */
  @media(max-width:780px){
    html{-webkit-text-size-adjust:100%}
    header{padding:8px 12px}
    .topbar{flex-wrap:wrap;gap:8px;align-items:center}
    .brand{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px}
    .search{order:3;flex:1 1 100%;font-size:16px;padding:10px 14px;margin-top:2px}
    .hbtns{order:2;flex-wrap:wrap;justify-content:flex-end;gap:6px}
    .hbtn{padding:6px 10px;font-size:12px}
    .readbtns button{padding:5px 8px;font-size:11px}
    /* 筛选：由横向滚动改为可换行，不再被截断 */
    .filters{overflow:visible;flex-wrap:wrap;gap:8px 10px;margin-top:8px;padding-bottom:0}
    .fgrp{flex-wrap:wrap}
    .chip{padding:5px 11px;font-size:12px}
    /* 网格：手机固定 2 列，更紧凑 */
    .wrap{padding:12px}
    .grid{grid-template-columns:repeat(2,1fr);gap:10px}
    .gcard-body{padding:8px 9px 10px}
    .gtitle{font-size:13px}
    .gsub{font-size:10.5px}
    .gridbar{margin:2px 0 10px}
    .sortbtns button{padding:4px 10px;font-size:11px}
    .cnt{font-size:12px}
    /* 详情 */
    #detailView{padding:14px 13px 56px}
    .dtitle{font-size:18px}
    .dsub{font-size:12px}
    .transcript{padding:12px;max-width:none}
    .meta-grid{grid-template-columns:1fr}
    .sec .t{font-size:11px}
    .summary{font-size:13px}
    /* 弹窗：宽度受限于视口，内容超高可滚动，操作钮吸底 */
    #ovModal .box{width:min(340px,92vw);padding:18px 16px;max-height:88vh;overflow:auto}
    #ovModal .acts{position:sticky;bottom:0;background:#fff;padding-top:12px;margin-top:14px}
    .pager{margin:18px 0 8px}
    .pager button{padding:9px 16px;font-size:14px}
    .pager .pginfo{font-size:13px}
    .dashcols{grid-template-columns:1fr;gap:12px}
  }
  @media(max-width:380px){
    .grid{gap:8px}
    .brand{font-size:13px}
    .hbtn{padding:5px 8px;font-size:11px}
  }
</style>
</head>
<body>
<header>
  <div class="topbar">
    <div class="brand"><span class="dot"></span>音声剧总册</div>
    <input class="search" id="search" placeholder="搜索：标题 / 说话人 / 台词 / 题材…">
    <div class="hbtns">
      <span class="readbtns" id="readBtns">
        <button data-rs="0.85">A−</button>
        <button data-rs="1" class="on">标准</button>
        <button data-rs="1.25">A+</button>
        <button data-rs="1.5">A++</button>
      </span>
      <button class="hbtn" id="dashBtn">数据总览</button>
      <button class="hbtn" id="editBtn">✎ 编辑台词</button>
    </div>
  </div>
  <div class="filters" id="filters"></div>
</header>
<div class="stats" id="stats"></div>
<div class="dash" id="dash">
  <div class="dashcols">
    <div><div class="dashh">题材标签（点击筛选）</div><div id="dashGenres" class="dashtags"></div></div>
    <div><div class="dashh">角色榜（点击筛选）</div><div id="dashSpeakers" class="dashtags"></div></div>
    <div><div class="dashh">强度分布（点击筛选）</div><div id="dashIntensity" class="dashtags"></div>
      <div style="margin-top:10px;font-size:12px;color:#64748b" id="dashHier"></div></div>
  </div>
  <div style="margin-top:10px"><button class="resetbtn" id="dashClear">清除总览筛选</button></div>
</div>
<div class="wrap" id="gridView"></div>
<div id="detailView" style="display:none"></div>

<div id="ovModal">
  <div class="box">
    <h3>手动纠错</h3>
    <div class="sub" id="ovSub"></div>
    <label>说话人（身份）</label>
    <input type="text" id="ovSpeaker" placeholder="如：哥哥 / 少女 / 主人…">
    <label>身份层级</label>
    <div class="rad">
      <label><input type="radio" name="ovHier" value="sup">上位者</label>
      <label><input type="radio" name="ovHier" value="sub">下位者</label>
      <label><input type="radio" name="ovHier" value="other">其他</label>
    </div>
    <label>语气 / 态度</label>
    <input type="text" id="ovTone" placeholder="如：命令 / 温柔 / 撒娇…">
    <div class="acts">
      <button class="cancel" id="ovReset" style="margin-right:auto;color:#b91c1c;border-color:#fecaca;background:#fef2f2">清空</button>
      <button class="cancel" id="ovCancel">取消</button>
      <button class="save" id="ovSave">保存</button>
    </div>
  </div>
</div>

__DATASCRIPTS__
<script>
const DATA = (window.__CAT__||[]).flat();
const TOTAL_CHANNEL = __TOTAL_CHANNEL__;
const DONE = DATA.length;
const ENRICHED = DATA.filter(r=>r.enriched).length;
const HAND = DATA.filter(r=>r.enriched && r.tier!=="auto").length;
const AUTO = DATA.filter(r=>r.enriched && r.tier==="auto").length;
const LINE_TOTAL = DATA.reduce((a,r)=>a+r.lines.length,0);

const state = {
  view:"grid", page:1, perPage:24, kw:"", sort:"default",
  filters:{ genre:null, intensity:null, hier:null, sensitive:null },
  selectedId:null
};

/* ===== 题材标签→主类（JS 侧，支持多归属） ===== */
const TAG2MAIN = {
  "主仆/调教":"主仆/调教","主仆":"主仆/调教","调教":"主仆/调教","BDSM":"主仆/调教","权力关系":"主仆/调教","权力":"主仆/调教","掌控":"主仆/调教","服从":"主仆/调教","训诫":"主仆/调教","惩罚":"主仆/调教","质问":"主仆/调教",
  "现代情侣":"现代情侣","现代":"现代情侣","情侣":"现代情侣","夫妻":"现代情侣","日常甜宠":"现代情侣","日常关怀":"现代情侣","日常":"现代情侣","调情":"现代情侣","吃醋":"现代情侣","信任":"现代情侣","晚归":"现代情侣","和好":"现代情侣","出走与挽留":"现代情侣","分离焦虑":"现代情侣","情书":"现代情侣","独白":"现代情侣","占有":"现代情侣",
  "校园/师生":"校园","校园":"校园","师生":"校园",
  "古风":"古风",
  "治愈":"治愈/宠溺","宠溺":"治愈/宠溺","安抚":"治愈/宠溺","安慰":"治愈/宠溺","情绪安抚":"治愈/宠溺","心疼":"治愈/宠溺","自伤关怀":"治愈/宠溺","管教后安抚":"治愈/宠溺","睡前":"治愈/宠溺",
  "家庭/长辈":"家庭/长辈","家庭":"家庭/长辈",
  "职场":"职场","金主":"职场",
  "医疗":"医疗",
  "宠物扮演":"宠物扮演"
};
const GENRE_LIST = ["主仆/调教","现代情侣","校园","古风","治愈/宠溺","家庭/长辈","职场","医疗","宠物扮演"];

function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
// 去掉频道前缀【Lの女性向音声】/【Lの】/【ASMR】
function cleanTitle(s){ return (s||"").replace(/^【(?:Lの女性向音声|Lの|ASMR)[^】]*】?\\s*/,"").trim(); }
// 拆分 "中文 (English)" → 主标题 + 副标题（英文）
function titlesOf(r){
  const raw = cleanTitle(r.title_zh || r.title);
  const m = raw.match(/^(.*?)\\s*\\(([^()]*)\\)\\s*$/);
  if(m) return {main:m[1].trim(), sub:m[2].trim()};
  return {main:raw, sub:""};
}

document.getElementById("stats").innerHTML =
  '结构化增强 <b>'+ENRICHED+' / '+DONE+'</b> 篇（'+Math.round(ENRICHED/DONE*100)+'%）· 精校 '+HAND+' · 自动 '+AUTO+
  ' · 台词 <b>'+LINE_TOTAL+'</b> 行 · 频道进度 '+DONE+' / '+TOTAL_CHANNEL+'（余 '+(TOTAL_CHANNEL-DONE)+' 篇因年龄墙待补）';

/* ===== 身份层级 / 语气 颜色映射（可手动纠错） ===== */
const HIER = {
  "哥哥":"sup","兄":"sup","兄长":"sup","お兄さん":"sup","主人":"sup","男友":"sup","老公":"sup","金主":"sup","老师":"sup",
  "彼":"sup","先辈":"sup","上司":"sup","先生":"sup","君":"sup","父":"sup","執事":"sup","执事":"sup","俺":"sup","夫君":"sup","爸爸":"sup",
  "爹地":"sup","爹":"sup","叔叔":"sup","继父":"sup","继兄":"sup","管家":"sup","医生":"sup","学长":"sup","殿下":"sup","陛下":"sup",
  "少爷":"sup","少主":"sup","公子":"sup","王爷":"sup","皇上":"sup","太子":"sup","影帝":"sup","总裁":"sup","老板":"sup","董事长":"sup",
  "警官":"sup","队长":"sup","教官":"sup","师父":"sup","师傅":"sup","长官":"sup","大人":"sup",
  "弟":"sub","弟弟":"sub","妹":"sub","妹妹":"sub","少女":"sub","私":"sub","后辈":"sub","部下":"sub","仆":"sub","僕":"sub","子":"sub","女":"sub",
  "宝贝":"sub","宝宝":"sub","小狗":"sub","狗狗":"sub","你":"sub","您":"sub"
};
// “他”是自动识别占位的统称（非真名字），按用户决策→中性灰（身份未确认），不假精确
function hierOf(name){
  if(!name) return "unknown";
  if(name==="他") return "unknown";
  if(HIER[name]==="sup") return "sup";
  if(HIER[name]==="sub") return "sub";
  return "other";
}
function hierColor(h){ if(h==="sup") return "#2563eb"; if(h==="sub") return "#db2777"; return "#64748b"; }
const TONE_COLOR = {
  "命令":"#dc2626","支配":"#dc2626","严厉":"#dc2626","叱":"#dc2626",
  "请求":"#ea580c","恳求":"#ea580c","哀求":"#ea580c",
  "询问":"#0d9488","疑惑":"#0d9488","疑问":"#0d9488",
  "温柔":"#0ea5e9","心疼":"#0ea5e9","安抚":"#0ea5e9","治愈":"#0ea5e9","溺爱":"#0ea5e9",
  "陈述":"#9ca3af","平静":"#9ca3af","平淡":"#9ca3af",
  "撒娇":"#a855f7","亲密":"#a855f7","宠溺":"#a855f7",
  "嘲讽":"#6b21a8","冷淡":"#6b21a8","戏谑":"#6b21a8","轻蔑":"#6b21a8"
};
function toneColor(t){ if(!t) return ""; for(const k in TONE_COLOR){ if(t.indexOf(k)>=0) return TONE_COLOR[k]; } return "#cbd5e1"; }
const NEUTRAL_TONE = /平静|陈述|平淡|中性/;

/* ===== 手动纠错覆盖（v2，旧 v1 自动清除） ===== */
const OV_KEY = "vdr_overrides_v2";
try { localStorage.removeItem("vdr_overrides_v1"); } catch(e){}
let OV = {};
try { OV = JSON.parse(localStorage.getItem(OV_KEY) || "{}"); } catch(e){ OV = {}; }
function saveOV(){ try { localStorage.setItem(OV_KEY, JSON.stringify(OV)); } catch(e){} }
function getOV(vid, li){ return (OV[vid] && OV[vid][li]) || null; }
function effSpeaker(r,i){ const ov=getOV(r.id,i); return (ov&&ov.speaker!==undefined)?ov.speaker:(r.lines[i]&&r.lines[i].speaker||""); }

// 阅读字号（全局 --rs）
const RS_KEY="vdr_readscale";
let READ_SCALE=1;
try{ const s=parseFloat(localStorage.getItem(RS_KEY)); if(s>=0.7&&s<=2) READ_SCALE=s; }catch(e){}
function applyReadScale(s){ READ_SCALE=s; document.documentElement.style.setProperty("--rs",s); try{localStorage.setItem(RS_KEY,String(s));}catch(e){} document.querySelectorAll("#readBtns button[data-rs]").forEach(b=>b.classList.toggle("on",parseFloat(b.dataset.rs)===s)); }
applyReadScale(READ_SCALE);

function hl(text,kw){
  if(!kw) return esc(text);
  const i = text.toLowerCase().indexOf(kw.toLowerCase());
  if(i<0) return esc(text);
  return esc(text.slice(0,i)) + "<mark>" + esc(text.slice(i,i+kw.length)) + "</mark>" + esc(text.slice(i+kw.length));
}
function fmtLine(t,kw){
  t = (t||"").trim();
  if(!t) return "";
  t = t.replace(/\\s+/g, "，");
  if(!/[。！？!?]$/.test(t)) t += "。";
  return hl(t, kw);
}
function tagsHTML(arr,kw){ return (arr||[]).map(t => '<span class="tag">'+hl(t,kw)+'</span>').join(''); }
function metaItem(k,v){ return '<div class="meta-item"><div class="k">'+esc(k)+'</div><div class="v">'+v+'</div></div>'; }

/* ===== 强度归一（7 种自由文本 → 高/中/低） ===== */
function normIntensity(s){
  if(!s) return "";
  if(s.indexOf("轻")>=0) return "低";
  let base = s.replace(/（.*?）/g,"").replace(/\\(.*?\\)/g,"").trim();
  if(base.indexOf("高")>=0) return "高";
  if(base.indexOf("中")>=0) return "中";
  if(base.indexOf("低")>=0) return "低";
  return base || "中";
}
function parseDur(d){
  d=(d||"").toString().trim();
  if(d.indexOf(":")>0){ const p=d.split(":"); let s=0; for(const x of p){ s=s*60+parseInt(x||"0",10);} return s; }
  let total=0; const fi=d.indexOf("分"); if(fi>0){ const n=parseInt(d.slice(0,fi),10); if(!isNaN(n)) total+=n*60; }
  const si=d.indexOf("秒"); if(si>0){ const n=parseInt(d.slice(fi+1,si),10); if(!isNaN(n)) total+=n; }
  return total;
}
function genreMains(r){ const set=new Set(); (r.genre_tags||[]).forEach(t=>{ const m=TAG2MAIN[t]; if(m) set.add(m); }); if(set.size===0) set.add("其他"); return [...set]; }
function primaryGenre(r){ const ms=genreMains(r); if(ms.length===1) return ms[0]; return ms.slice().sort((a,b)=>(GENRE_COUNT[b]||0)-(GENRE_COUNT[a]||0))[0]; }

/* ===== 全局聚合（题材用多归属计数，合计可超 DONE） ===== */
const GENRE_COUNT={}, SPEAKER_COUNT={}, INTENSITY_COUNT={};
const HIER_TOTAL={sup:0,sub:0,other:0,unknown:0};
DATA.forEach(r=>{
  genreMains(r).forEach(g=>{ GENRE_COUNT[g]=(GENRE_COUNT[g]||0)+1; });
  const ni=normIntensity(r.intensity); if(ni) INTENSITY_COUNT[ni]=(INTENSITY_COUNT[ni]||0)+1;
  (r.lines||[]).forEach((l,i)=>{ const s=effSpeaker(r,i); if(s){ SPEAKER_COUNT[s]=(SPEAKER_COUNT[s]||0)+1; HIER_TOTAL[hierOf(s)]++; } });
});
const TOP_GENRES=Object.entries(GENRE_COUNT).sort((a,b)=>b[1]-a[1]);
const TOP_SPEAKERS=Object.entries(SPEAKER_COUNT).sort((a,b)=>b[1]-a[1]).slice(0,30);

/* ===== 搜索：同义词扩展 + 多字段命中 ===== */
const SYNONYMS = {
  "哥哥":["兄长","お兄さん","哥","兄"],"主人":["主","主人公"],"管娇":["打手心","OTK","巴掌","戒尺","管教","惩戒","spanking"],
  "调教":["训练","规训"],"撒娇":["娇","黏人","黏"],"宠溺":["溺爱","宠","宠爱"],"温柔":["温软","安抚","心疼","治愈"],
  "男友":["老公","对象","先生"],"老师":["师父","师傅"],"爸爸":["爹地","父亲"],"宝宝":["宝贝","小狗","狗狗"],
  "命令":["支配","严厉","叱责"],"请求":["恳求","哀求"],"询问":["疑惑","疑问"],"冷淡":["嘲讽","轻蔑","戏谑"]
};
function expandKw(kw){
  kw=(kw||"").trim().toLowerCase();
  if(!kw) return [];
  let arr=[kw];
  for(const k in SYNONYMS){
    const kl=k.toLowerCase();
    if(kw.indexOf(kl)>=0 || SYNONYMS[k].some(s=>kw.indexOf(s.toLowerCase())>=0)) arr.push(...SYNONYMS[k].map(s=>s.toLowerCase()));
  }
  return [...new Set(arr)];
}
function kwHit(r,kws){
  if(!kws.length) return true;
  const low = s=>(s||"").toLowerCase();
  return kws.some(k =>
    low(cleanTitle(r.title)).indexOf(k)>=0 || low(cleanTitle(r.title_zh)).indexOf(k)>=0 || low(r.scene).indexOf(k)>=0 ||
    (r.behaviors||[]).some(b=>low(b.desc).indexOf(k)>=0) ||
    (r.lines||[]).some(l=>low(l.text).indexOf(k)>=0||low(l.speaker).indexOf(k)>=0||low(l.tone).indexOf(k)>=0||(l.sound||[]).some(s=>low(s).indexOf(k)>=0)) ||
    low(r.tone_summary).indexOf(k)>=0 || (r.genre_tags||[]).some(t=>low(t).indexOf(k)>=0) || low(r.listener_role).indexOf(k)>=0 || (r.signature_elements||[]).some(t=>low(t).indexOf(k)>=0)
  );
}

/* ===== 过滤 + 排序 ===== */
function applyFilters(list){
  const kws = expandKw(state.kw);
  return list.filter(r=>{
    if(state.filters.genre && !genreMains(r).includes(state.filters.genre)) return false;
    if(state.filters.intensity && normIntensity(r.intensity)!==state.filters.intensity) return false;
    if(state.filters.hier){ const ok=(r.lines||[]).some((l,i)=>hierOf(effSpeaker(r,i))===state.filters.hier); if(!ok) return false; }
    if(state.filters.sensitive==="y" && !r.sensitive) return false;
    if(state.filters.sensitive==="n" && r.sensitive) return false;
    if(kws.length && !kwHit(r,kws)) return false;
    return true;
  });
}
function applySortGrid(list){
  const arr=list.slice();
  if(state.sort==="dur") arr.sort((a,b)=>parseDur(a.duration)-parseDur(b.duration));
  else if(state.sort==="intensity"){ const o={"高":0,"中":1,"低":2}; arr.sort((a,b)=>(o[normIntensity(a.intensity)]??9)-(o[normIntensity(b.intensity)]??9)); }
  else arr.sort((a,b)=>(a.no||0)-(b.no||0));
  return arr;
}

/* ===== 网格卡片 ===== */
function gridCardHTML(r,kw){
  const tt=titlesOf(r);
  const id=r.id;
  const thumb="https://i.ytimg.com/vi/"+encodeURIComponent(id)+"/mqdefault.jpg";
  const badge = !r.enriched ? '<span class="badge base">基础</span>'
    : (r.tier==="auto" ? '<span class="badge auto">⚙ 自动</span>' : '<span class="badge ok">✓ 精校</span>');
  const pg=primaryGenre(r);
  const inten=normIntensity(r.intensity);
  let chips="";
  if(pg&&pg!=="其他") chips+='<span class="pill">'+hl(pg,kw)+'</span>';
  if(inten) chips+='<span class="pill">'+hl(inten,kw)+'</span>';
  if(r.sensitive) chips+='<span class="pill warn">敏感</span>';
  const dur=r.duration?'<span class="meta">'+esc(r.duration)+'</span>':'';
  const init=(tt.main||id).charAt(0);
  return '<a class="gcard" data-id="'+esc(id)+'" href="#v='+encodeURIComponent(id)+'">'+
    '<div class="thumb"><img loading="lazy" src="'+thumb+'" alt="" onerror="imgFail(this)"><div class="tf" style="display:none">'+esc(init)+'</div></div>'+
    '<div class="gcard-body">'+
      '<div class="gtitle">'+hl(tt.main,kw)+'</div>'+
      (tt.sub?'<div class="gsub">'+hl(tt.sub,kw)+'</div>':'')+
      '<div class="gmeta">'+chips+dur+'</div>'+
      '<div style="margin-top:6px">'+badge+'</div>'+
    '</div>'+
  '</a>';
}
function imgFail(img){ img.style.display="none"; const tf=img.parentNode.querySelector(".tf"); if(tf) tf.style.display="flex"; }

function sortHTML(){
  const opts=[["default","最新"],["dur","时长↑"],["intensity","强度↓"]];
  return '<span class="sortbtns">'+opts.map(o=>'<button data-sort="'+o[0]+'" class="'+(state.sort===o[0]?"on":"")+'">'+o[1]+'</button>').join("")+'</span>';
}
function pagerHTML(pages,total){
  if(pages<=1) return "";
  const prev = state.page>1 ? '<button data-page="'+(state.page-1)+'">← 上一页</button>' : '<button disabled>← 上一页</button>';
  const next = state.page<pages ? '<button data-page="'+(state.page+1)+'">下一页 →</button>' : '<button disabled>下一页 →</button>';
  return '<div class="pager">'+prev+'<span class="pginfo">第 '+state.page+' / '+pages+' 页 · 共 '+total+' 篇</span>'+next+'</div>';
}
function renderGrid(){
  const filtered=applySortGrid(applyFilters(DATA));
  const total=filtered.length;
  const pages=Math.max(1,Math.ceil(total/state.perPage));
  if(state.page>pages) state.page=pages;
  const start=(state.page-1)*state.perPage;
  const items=filtered.slice(start,start+state.perPage);
  let html='<div class="gridbar"><span class="cnt">共 <b>'+total+'</b> 篇'+(state.kw?' · 搜索“'+esc(state.kw)+'”':'')+'</span>'+sortHTML()+'</div>';
  if(total===0) html+='<div class="empty" style="padding:40px;text-align:center">没有匹配的篇目，试试放宽筛选条件。</div>';
  else html+='<div class="grid">'+items.map(r=>gridCardHTML(r,state.kw)).join("")+'</div>';
  html+=pagerHTML(pages,total);
  const gv=document.getElementById("gridView");
  gv.innerHTML=html; gv.style.display="block";
  document.getElementById("detailView").style.display="none";
  state.view="grid";
}

/* ===== 详情视图（单篇完整台词，剧本视图） ===== */
function openDetail(id){
  const r=DATA.find(x=>x.id===id); if(!r) return;
  state.selectedId=id;
  renderDetail(r);
  document.getElementById("gridView").style.display="none";
  const dv=document.getElementById("detailView");
  dv.style.display="block";
  state.view="detail";
  window.scrollTo(0,0);
}
function lineMeta(r,i){
  const l=r.lines[i]; if(!l) return null;
  const ov=getOV(r.id,i);
  const speaker=(ov&&ov.speaker!==undefined)?ov.speaker:(l.speaker||"");
  const tone=(ov&&ov.tone!==undefined)?ov.tone:(l.tone||"");
  const hier=(ov&&ov.hier)?ov.hier:hierOf(speaker);
  return {l,speaker,tone,hier};
}
/* 剧本体渲染：story 数组 [{type:narr|line,text,speaker?}]，叙述灰色、台词按说话人层级着色 */
function storyHTML(r,kw){
  const st=r.story||[];
  if(!st.length) return '';
  let out="";
  for(let i=0;i<st.length;i++){
    const s=st[i]; if(!s||!s.text) continue;
    if(s.type==="narr"){
      out+='<span class="sn">'+hl(s.text,kw)+'</span>';
    }else{
      const spk=s.speaker||"";
      const hier=spk?hierOf(spk):"other";
      const color=spk?hierColor(hier):"";
      const spkSpan=spk?'<span class="spk" data-hier="'+hier+'" style="color:'+color+'">'+hl(spk,kw)+'：</span>':'';
      const toneCls=s.tone&&!NEUTRAL_TONE.test(s.tone)&&toneColor(s.tone)?' style="color:'+toneColor(s.tone)+'"':'';
      out+='<span class="sl"><span class="st"'+toneCls+'>'+spkSpan+hl(s.text,kw)+'</span></span>';
    }
  }
  return '<div class="story">'+out+'</div>';
}
/* 台词分段模式：按说话人归组为段落（长独白按 ~10 句切分），说话人标签仅出现一次；
   每行仍是一个 .dl 可点击元素，保留逐句纠错能力。 */
function detailParasHTML(r,kw){
  const lines=r.lines||[];
  if(!lines.length) return '<div class="empty">（无台词）</div>';
  const CAP=10; let out=""; let i=0;
  while(i<lines.length){
    const sp=lineMeta(r,i).speaker;
    const run=[]; let j=i;
    while(j<lines.length && lineMeta(r,j).speaker===sp){ run.push(j); j++; }
    for(let c=0;c<run.length;c+=CAP){
      const chunk=run.slice(c,c+CAP);
      const first=chunk[0]; const fm=lineMeta(r,first);
      const hier=fm.hier;
      let barColor="";
      for(const idx of chunk){ const m=lineMeta(r,idx); const tc=toneColor(m.tone); const neutral=m.tone&&NEUTRAL_TONE.test(m.tone); if(tc&&!neutral){ barColor=tc; break; } }
      const bar=barColor?' style="border-left-color:'+barColor+'"':'';
      const spk=fm.speaker;
      const spkSpan=spk?'<span class="spk line-speaker" data-hier="'+hier+'" data-vid="'+esc(r.id)+'" data-li="'+first+'">'+hl(spk,kw)+'</span>':'';
      let body="";
      for(const idx of chunk){
        const m=lineMeta(r,idx);
        const text=fmtLine(m.l.text,kw);
        const snd=(m.l.sound||[]).map(s=>'<span class="snd">'+hl(s,kw)+'</span>').join(" ");
        body+='<span class="dl" data-vid="'+esc(r.id)+'" data-li="'+idx+'">'+text+(snd?' '+snd:'')+'</span> ';
      }
      out+='<div class="dpara"'+bar+'>'+spkSpan+'<div class="diatext">'+body+'</div></div>';
    }
    i=j;
  }
  return out;
}
function metaHTML(r,kw){
  if(!r.enriched) return '';
  const parts=[];
  if(r.tone_summary){ const cls=r.sensitive?' class="sensitive"':''; parts.push(metaItem('语气总结','<span'+cls+'>'+hl(r.tone_summary,kw)+'</span>')); }
  if((r.genre_tags||[]).length) parts.push(metaItem('题材 / 关系', tagsHTML(r.genre_tags,kw)));
  if(r.emotion_arc) parts.push(metaItem('情感弧线', hl(r.emotion_arc,kw)));
  if(r.intensity) parts.push(metaItem('强度', hl(r.intensity,kw)));
  if(r.listener_role) parts.push(metaItem('听者角色', hl(r.listener_role,kw)));
  if((r.signature_elements||[]).length) parts.push(metaItem('标志性元素', tagsHTML(r.signature_elements,kw)));
  if(!parts.length) return '';
  return '<div class="sec"><div class="t">内容分析</div><div class="meta-grid">'+parts.join('')+'</div></div>';
}
function renderDetail(r){
  const tt=titlesOf(r);
  const badge = !r.enriched ? '<span class="badge base">基础版</span>'
    : (r.tier==="auto"?'<span class="badge auto">⚙ 自动增强</span>':'<span class="badge ok">✓ 精校增强</span>');
  const pg=primaryGenre(r); const inten=normIntensity(r.intensity);
  let chips="";
  if(pg&&pg!=="其他") chips+='<span class="pill">'+esc(pg)+'</span>';
  if(inten) chips+='<span class="pill">'+esc(inten)+'</span>';
  if(r.sensitive) chips+='<span class="pill warn">敏感内容</span>';
  const meta='<span class="meta">'+esc(r.duration)+' · <a href="'+esc(r.link)+'" target="_blank" rel="noopener">YouTube 原片 ↗</a></span>';
  let sp=[];
  if(r.scene) sp.push(esc(r.scene));
  if(r.emotion_arc) sp.push('情感弧：'+esc(r.emotion_arc));
  const summary = sp.length? sp.join('<span class="sep">·</span>') : '<span class="empty">（无场景描述）</span>';
  const lines=(r.story&&r.story.length)?storyHTML(r,state.kw):detailParasHTML(r,state.kw);
  const linesSec=r.story&&r.story.length?'台词（剧本体 · 彩色为台词）':'台词（剧本视图）';
  const meta2=metaHTML(r,state.kw);
  const beh=(r.behaviors||[]).map((b,i)=>'<li><span class="num">'+String(i+1)+'.</span><span>'+hl(b.desc,state.kw)+'</span></li>').join("");
  const behHTML=beh?'<div class="sec"><div class="t">行为节点</div><ul class="beh">'+beh+'</ul></div>':'';
  const enhHint=r.enriched?'':'<div class="summary" style="margin-top:12px">本篇尚未叠加说话人/语气/音效/分析字段，完成增强后将自动更新。</div>';
  const html='<button class="backbtn" data-back>← 返回总册</button>'+
    '<h1 class="dtitle">'+hl(tt.main,state.kw)+'</h1>'+
    (tt.sub?'<div class="dsub">'+hl(tt.sub,state.kw)+'</div>':'')+
    '<div class="dmetarow">'+badge+' '+chips+' '+meta+'</div>'+
    '<div class="summary">'+summary+'</div>'+
    '<div class="sec"><div class="t">'+linesSec+'</div><div class="transcript">'+lines+'</div></div>'+
    meta2+behHTML+enhHint;
  document.getElementById("detailView").innerHTML=html;
}

/* ===== 顶部筛选条 ===== */
const FILTER_DEFS=[
  {dim:"genre",label:"题材",opts:GENRE_LIST.map(g=>[g,g])},
  {dim:"intensity",label:"强度",opts:[["高","高"],["中","中"],["低","低"]]},
  {dim:"hier",label:"身份",opts:[["sup","上位者"],["sub","下位者"],["other","其他"]]},
  {dim:"sensitive",label:"敏感",opts:[["y","仅敏感"],["n","仅非敏感"]]}
];
function renderFilters(){
  const box=document.getElementById("filters");
  box.innerHTML=FILTER_DEFS.map(f=>
    '<span class="fgrp"><b>'+f.label+'：</b>'+
    '<span class="chip'+(state.filters[f.dim]?'':' on')+'" data-dim="'+f.dim+'" data-val="">全部</span>'+
    f.opts.map(o=>'<span class="chip'+(state.filters[f.dim]===o[0]?' on':'')+'" data-dim="'+f.dim+'" data-val="'+o[0]+'">'+o[1]+'</span>').join("")+
    '</span>').join("");
}

/* ===== 数据总览面板 ===== */
function renderDash(){
  const total=DONE;
  const gHtml=TOP_GENRES.slice(0,24).map(([t,c])=>{
    const fs=11+Math.min(5,Math.round(c/total*40));
    return '<button class="dtag'+(state.filters.genre===t?' on':'')+'" data-kind="genre" data-val="'+esc(t)+'" style="font-size:'+fs+'px">'+esc(t)+' <b>'+c+'</b></button>';
  }).join("");
  const sHtml=TOP_SPEAKERS.map(([s,c])=>{
    const h=hierOf(s);
    const color=h==="sup"?"#2563eb":h==="sub"?"#db2777":"#94a3b8";
    return '<button class="dspk" data-kind="speaker" data-val="'+esc(s)+'"><span style="color:'+color+'">●</span> '+esc(s)+' <b>'+c+'</b></button>';
  }).join("");
  const iHtml=Object.keys(INTENSITY_COUNT).sort().map(k=>{
    const c=INTENSITY_COUNT[k];
    const color=k==="高"?"#dc2626":k==="中"?"#ea580c":"#0d9488";
    return '<button class="dtag'+(state.filters.intensity===k?' on':'')+'" data-kind="intensity" data-val="'+esc(k)+'" style="border-color:'+color+';color:'+color+'">'+esc(k)+' <b>'+c+'</b></button>';
  }).join("");
  document.getElementById("dashGenres").innerHTML=gHtml||'<span class="empty">（无）</span>';
  document.getElementById("dashSpeakers").innerHTML=sHtml||'<span class="empty">（无）</span>';
  document.getElementById("dashIntensity").innerHTML=iHtml||'<span class="empty">（无）</span>';
  const hT=HIER_TOTAL;
  document.getElementById("dashHier").innerHTML='全库身份格局：上位 <b style="color:#2563eb">'+hT.sup+'</b> · 下位 <b style="color:#db2777">'+hT.sub+'</b> · 其他 <b style="color:#475569">'+hT.other+'</b> · 未识别 '+hT.unknown+'（"他"为自动识别占位，按中性灰计）';
}
function syncTopChips(){
  document.querySelectorAll('#filters .chip').forEach(c=>{
    const dim=c.dataset.dim, val=c.dataset.val;
    const on=(!state.filters[dim] && val==="") || (state.filters[dim]===val);
    c.classList.toggle("on",on);
  });
}
function syncDash(){
  document.querySelectorAll('#dashGenres .dtag').forEach(b=>b.classList.toggle('on', b.dataset.val===state.filters.genre));
  document.querySelectorAll('#dashIntensity .dtag').forEach(b=>b.classList.toggle('on', b.dataset.val===state.filters.intensity));
}

/* ===== 事件绑定 ===== */
document.getElementById("filters").addEventListener("click",e=>{
  const ch=e.target.closest(".chip"); if(!ch) return;
  const dim=ch.dataset.dim, val=ch.dataset.val;
  state.filters[dim]=(state.filters[dim]===val && val!=="")?null:val;
  const grp=ch.parentElement;
  grp.querySelectorAll(".chip").forEach(c=>c.classList.remove("on"));
  if(!state.filters[dim]) grp.querySelector('[data-val=""]').classList.add("on");
  else ch.classList.add("on");
  syncDash(); state.page=1; renderGrid();
});
document.getElementById("dashBtn").addEventListener("click",()=>{
  const d=document.getElementById("dash");
  const open=d.classList.toggle("open");
  document.getElementById("dashBtn").classList.toggle("on",open);
  if(open) renderDash();
});
document.getElementById("dash").addEventListener("click",e=>{
  const b=e.target.closest("[data-kind]"); if(!b) return;
  const kind=b.dataset.kind, val=b.dataset.val;
  if(kind==="genre") state.filters.genre=(state.filters.genre===val)?null:val;
  else if(kind==="intensity") state.filters.intensity=(state.filters.intensity===val)?null:val;
  syncTopChips(); syncDash(); state.page=1; renderGrid();
});
document.getElementById("dashClear").addEventListener("click",()=>{
  state.filters.genre=null; state.filters.intensity=null;
  syncTopChips(); syncDash(); state.page=1; renderGrid();
});
// 全局点击：卡片 / 分页 / 排序 / 返回
document.addEventListener("click",e=>{
  const card=e.target.closest(".gcard");
  if(card){ location.hash="#v="+encodeURIComponent(card.dataset.id); return; }
  const p=e.target.closest("[data-page]");
  if(p){ state.page=+p.dataset.page; window.scrollTo(0,0); renderGrid(); return; }
  const s=e.target.closest("[data-sort]");
  if(s){ state.sort=s.dataset.sort; renderGrid(); return; }
  const b=e.target.closest("[data-back]");
  if(b){ location.hash=""; return; }
});
// 搜索（防抖 180ms）
let searchTimer=null;
document.getElementById("search").addEventListener("input",e=>{
  clearTimeout(searchTimer);
  const v=e.target.value;
  searchTimer=setTimeout(()=>{ state.kw=v; state.page=1; renderGrid(); },180);
});
// 字号
document.getElementById("readBtns").addEventListener("click",e=>{
  const b=e.target.closest("button[data-rs]"); if(!b) return;
  applyReadScale(parseFloat(b.dataset.rs));
});
// hash 路由
function onHash(){
  const m=location.hash.match(/^#v=(.+)$/);
  if(m) openDetail(decodeURIComponent(m[1]));
  else renderGrid();
}
window.addEventListener("hashchange",onHash);

/* ===== 编辑模式 + 纠错弹窗 ===== */
let EDIT=false;
function toggleEdit(){
  EDIT=!EDIT; document.body.classList.toggle("edit",EDIT);
  const btn=document.getElementById("editBtn");
  btn.classList.toggle("on",EDIT); btn.textContent=EDIT?"✎ 编辑：开":"✎ 编辑台词";
}
function openEditor(vid,li,curSpeaker,curHier,curTone){
  const m=document.getElementById("ovModal");
  m.dataset.vid=vid; m.dataset.li=li;
  document.getElementById("ovSub").textContent="视频 #"+vid+" · 第 "+(li+1)+" 句";
  document.getElementById("ovSpeaker").value=curSpeaker||"";
  const hv=curHier||hierOf(curSpeaker);
  const rad=document.querySelector('input[name=ovHier][value="'+hv+'"]');
  if(rad) rad.checked=true;
  document.getElementById("ovTone").value=curTone||"";
  m.style.display="flex"; document.getElementById("ovSpeaker").focus();
}
function closeEditor(){ document.getElementById("ovModal").style.display="none"; }
function saveEditor(){
  const m=document.getElementById("ovModal");
  const vid=m.dataset.vid, li=+m.dataset.li;
  const speaker=document.getElementById("ovSpeaker").value.trim();
  const checked=document.querySelector('input[name=ovHier]:checked');
  const hier=checked?checked.value:hierOf(speaker);
  const tone=document.getElementById("ovTone").value.trim();
  if(!OV[vid]) OV[vid]={};
  OV[vid][li]={speaker,hier,tone};
  saveOV(); closeEditor();
  if(state.view==="detail" && state.selectedId===vid) renderDetail(DATA.find(r=>r.id===vid));
  else renderGrid();
}
document.getElementById("editBtn").addEventListener("click",toggleEdit);
document.getElementById("ovSave").addEventListener("click",saveEditor);
document.getElementById("ovCancel").addEventListener("click",closeEditor);
document.getElementById("ovReset").addEventListener("click",()=>{
  if(confirm("确定清空所有手动纠错？（仅清除本地覆盖，不影响原始数据）")){
    OV={}; saveOV();
    if(state.view==="detail") renderDetail(DATA.find(r=>r.id===state.selectedId));
    else renderGrid();
  }
});
document.addEventListener("click",e=>{
  if(!EDIT) return;
  const t=e.target.closest(".line-speaker,.dl");
  if(!t) return;
  const vid=t.dataset.vid, li=+t.dataset.li;
  const rec=DATA.find(r=>r.id===vid); if(!rec) return;
  const l=rec.lines[li]; const ov=getOV(vid,li);
  const speaker=(ov&&ov.speaker!==undefined)?ov.speaker:(l.speaker||"");
  const hier=(ov&&ov.hier)?ov.hier:hierOf(speaker);
  const tone=(ov&&ov.tone!==undefined)?ov.tone:(l.tone||"");
  openEditor(vid,li,speaker,hier,tone);
});

/* ===== 初始化 ===== */
renderFilters();
if(location.hash.match(/^#v=(.+)$/)) onHash();
else renderGrid();
</script>
</body>
</html>
"""

# ── 分块写入 catalog_data/*.js（绕过沙箱 ~250KB 单请求体上传限制）──
import os as _os
_datadir = _os.path.join(BASE, "catalog_data")
_os.makedirs(_datadir, exist_ok=True)
for _fn in _os.listdir(_datadir):
    if _fn.startswith("part_") and _fn.endswith(".js"):
        try: _os.remove(_os.path.join(_datadir, _fn))
        except: pass
CHUNK = 150 * 1024  # raw 字节上限；base64 后 ~200KB，远低于沙箱 ~333KB 代理限制
parts = []; cur = []; size = 0
for rec in records:
    s = len(json.dumps(rec, ensure_ascii=False).encode("utf-8"))
    if size + s > CHUNK and cur:
        parts.append(cur); cur = []; size = 0
    cur.append(rec); size += s
if cur:
    parts.append(cur)
part_files = []
for i, p in enumerate(parts, 1):
    fn = f"part_{i:03d}.js"
    with open(_os.path.join(_datadir, fn), "w", encoding="utf-8") as _f:
        # 防 </script> 注入，与内联时一致
        _f.write("window.__CAT__=window.__CAT__||[];window.__CAT__.push(" +
                 json.dumps(p, ensure_ascii=False).replace("</", "<\\/") + ");")
    part_files.append(fn)
INLINE = os.environ.get("INLINE") == "1"
if INLINE:
    # 单文件内联版：把分块数据塞进一个 <script>，去掉子请求，
    # 用于部署到国内可访问的托管（github.io 在大陆常拉不全分块导致空白）。
    data_js = "\n".join(open(_os.path.join(_datadir, fn), encoding="utf-8").read() for fn in part_files)
    scripts = '<script>\n' + data_js + '\n</script>'
    out = os.path.join(BASE, "mrlovewords9272_catalog_standalone.html")
else:
    scripts = "".join(f'<script src="catalog_data/{fn}"></script>' for fn in part_files)
    out = os.path.join(BASE, "mrlovewords9272_catalog.html")
HTML = HTML.replace("__DATASCRIPTS__", scripts)
HTML = HTML.replace("__DATA__", "")
HTML = HTML.replace("__TOTAL_CHANNEL__", str(TOTAL_CHANNEL))

with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)

print("data parts:", len(part_files), "| written:", out)

print("written:", out)
print("size MB: %.2f" % (os.path.getsize(out)/1024/1024))
print("records:", len(records), "| enriched:", enriched_count, "| lines:", line_count, "| behaviors:", behavior_count)
