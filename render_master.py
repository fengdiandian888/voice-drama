#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the Lの系列音声剧 225-篇 Structured Catalog (同步增强版).

数据源:
  - doc_data/videos_simp.json   (225篇基础台词, 已系统错别字校对)
  - doc_data/behavior_simp.json (场景 + 行为节点)
  - doc_data/enriched/chunk_*.json (已完成"一次性调整"的篇: 说话人/语气/音效/篇级分析)
合并规则: 每篇默认用基础数据; 若 enriched 中存在同 id, 则叠加新字段并标记 enriched.

交互功能 (v2 新增):
  - 说话人身份层级配色: 上位者=蓝 / 下位者=粉 / 其他=灰 / 未识别=虚线灰
  - 语气态度配色: 左侧 4px 色条 + 语气标签底色 (命令红/请求橙/询问青/温柔蓝/平静灰/撒娇紫/冷淡暗紫 ...)
  - 手动纠错: 编辑模式开启后, 点击任意说话人/语气标签弹出修正框, 覆盖存于浏览器 localStorage
"""
import json, os, glob

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
            "emotion_arc": e.get("emotion_arc", ""),
            "intensity": e.get("intensity", ""),
            "listener_role": e.get("listener_role", ""),
            "signature_elements": e.get("signature_elements", []),
            "sensitive": bool(e.get("sensitive", False)),
            "tier": e.get("tier", "hand"),
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
    --bg:#f6f7f9; --panel:#ffffff; --ink:#1f2329; --sub:#6b7280;
    --line:#e5e7eb; --accent:#2563eb; --accent2:#0ea5e9;
    --tag:#eef2ff; --barbg:#e5e7eb; --ok:#16a34a;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
       background:var(--bg);color:var(--ink);font-size:14px;line-height:1.6}
  header{position:sticky;top:0;z-index:50;background:var(--panel);border-bottom:1px solid var(--line);
         padding:12px 20px;box-shadow:0 1px 4px rgba(0,0,0,.04)}
  h1{font-size:17px;margin:0 0 8px;font-weight:700}
  .progress-wrap{display:flex;gap:24px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
  .prog{display:flex;flex-direction:column;gap:3px;min-width:220px}
  .prog .lab{font-size:12px;color:var(--sub)}
  .prog .val{font-size:13px;font-weight:600}
  .bar{height:8px;background:var(--barbg);border-radius:6px;overflow:hidden}
  .bar > i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:6px}
  .bar.full > i{background:var(--ok)}
  .stats{font-size:12px;color:var(--sub);margin-left:auto;text-align:right}
  .search{width:100%;padding:9px 12px;border:1px solid var(--line);border-radius:8px;font-size:14px;outline:none}
  .search:focus{border-color:var(--accent)}
  .filters{display:flex;flex-wrap:wrap;gap:10px 16px;margin:10px 0 2px}
  .filters .fgrp{display:flex;align-items:center;gap:6px;font-size:12px;color:#64748b}
  .filters .fgrp>b{color:#475569}
  .chip{cursor:pointer;padding:2px 10px;border-radius:999px;border:1px solid #e2e8f0;background:#fff;color:#475569;font-size:12px;user-select:none;transition:.12s}
  .chip:hover{border-color:#2563eb;color:#2563eb}
  .chip.on{background:#2563eb;color:#fff;border-color:#2563eb}
  .legend{font-size:11px;color:var(--sub);display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px}
  .legend .grp{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
  .legend .it{display:flex;align-items:center;gap:4px}
  .legend .sw{width:12px;height:12px;border-radius:3px;display:inline-block}
  .editbtn{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:6px;padding:3px 10px;font-size:12px;color:var(--ink)}
  .editbtn:hover{border-color:var(--accent)}
  .editbtn.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .resetbtn{cursor:pointer;border:none;background:none;color:var(--sub);font-size:11px;text-decoration:underline;padding:0 4px}
  .layout{display:flex;align-items:flex-start;max-width:1280px;margin:0 auto}
  nav.toc{position:sticky;top:148px;width:250px;flex:0 0 250px;height:calc(100vh - 148px);
          overflow-y:auto;padding:14px 8px 40px;border-right:1px solid var(--line)}
  nav.toc a{display:block;padding:5px 10px;border-radius:6px;color:var(--ink);text-decoration:none;
            font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  nav.toc a:hover{background:var(--tag);color:var(--accent)}
  main{flex:1;padding:18px 22px 80px;min-width:0}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:18px;
        scroll-margin-top:160px}
  .card h2{font-size:15px;margin:0 0 4px;font-weight:700;display:flex;align-items:center;flex-wrap:wrap}
  .card .meta{font-size:12px;color:var(--sub);margin-bottom:10px}
  .card .meta a{color:var(--accent);text-decoration:none}
  .sec{margin-top:12px}
  .sec .t{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:.04em;
          border-left:3px solid var(--accent);padding-left:8px;margin-bottom:5px}
  .scene{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:10px 12px;color:#374151}
  ul.beh{list-style:none;margin:0;padding:0}
  ul.beh li{display:flex;gap:10px;padding:4px 0;border-bottom:1px dashed var(--line);font-size:13px}
  ul.beh li:last-child{border-bottom:none}
  ul.beh li .num{flex:0 0 30px;color:var(--accent2);font-weight:600}
  .transcript{max-height:360px;overflow-y:auto;background:#fbfcfe;border:1px solid var(--line);
              border-radius:8px;padding:10px 12px}
  .tline{margin:0 0 9px;padding:2px 0 2px 10px;font-size:13.5px;color:#374151;text-align:justify;line-height:1.75;
         border-left:4px solid transparent}
  .tline:last-child{margin-bottom:0}
  .empty{color:var(--sub);font-style:italic}
  mark{background:#fde68a;border-radius:2px}
  .badge{display:inline-block;border-radius:999px;font-size:11px;padding:1px 9px;margin-left:8px;font-weight:600;vertical-align:middle}
  .badge.ok{background:#dcfce7;color:#16a34a}
  .badge.auto{background:#fef3c7;color:#b45309}
  .badge.base{background:#f1f5f9;color:#94a3b8}
  /* 说话人 / 语气 / 音效 旧样式保留（纠错弹窗用色一致），仅默认视图不再用药丸堆叠 */
  .line-speaker{display:inline-block;border-radius:4px;font-size:11px;padding:0 5px;margin-right:4px;font-weight:700}
  .line-speaker[data-hier="sup"]{color:#2563eb;background:#eff6ff}
  .line-speaker[data-hier="sub"]{color:#db2777;background:#fdf2f8}
  .line-speaker[data-hier="other"]{color:#4b5563;background:#f3f4f6}
  .line-speaker[data-hier="unknown"]{color:#9ca3af;background:#f9fafb;border:1px dashed #cbd5e1}
  .line-tone{display:inline-block;border-radius:4px;font-size:11px;padding:0 5px;margin-right:4px;font-weight:600;color:#fff}
  .line-sound{display:inline-block;background:#fce7f3;color:#be185d;border-radius:4px;font-size:11px;padding:0 5px;margin-left:3px;font-weight:600}
  body.edit .line-speaker{cursor:pointer;outline:1px dashed #cbd5e1;outline-offset:1px}
  body.edit .line-speaker:hover{filter:brightness(.95)}

  /* ── 台词三视图（统一用 .line-speaker 承载，先中和旧药丸底色）── */
  .transcript .line-speaker{background:none!important;border:none!important;padding:0;margin:0;font-weight:500;border-radius:0}

  .transcript.view-script .tline{display:grid;grid-template-columns:52px 1fr;gap:2px 12px;align-items:baseline;margin:0;padding:6px 0;border-top:1px solid #f1f5f9}
  .transcript.view-script .tline:first-child{border-top:none}
  .transcript.view-script .line-speaker{display:block;text-align:right;font-size:13px;white-space:nowrap}
  .transcript.view-script .line-speaker[data-hier="sup"]{color:#2563eb}
  .transcript.view-script .line-speaker[data-hier="sub"]{color:#db2777}
  .transcript.view-script .line-speaker[data-hier="other"]{color:#4b5563}
  .transcript.view-script .line-speaker[data-hier="unknown"]{color:#9ca3af}
  .transcript.view-script .dia{padding-left:10px;border-left:3px solid #e2e8f0;font-size:13px;line-height:1.7;color:#1e293b}
  .transcript.view-script .dia[data-tc]{border-left-color:var(--tc)}
  .transcript.view-script .snd{color:#94a3b8;font-size:11px;margin-left:4px}

  .transcript.view-bubble{display:flex;flex-direction:column;gap:8px;padding:6px 0}
  .transcript.view-bubble .tline{display:flex;margin:0}
  .transcript.view-bubble .tline[data-h="sup"]{justify-content:flex-start}
  .transcript.view-bubble .tline[data-h="sub"]{justify-content:flex-end}
  .transcript.view-bubble .tline[data-h="other"],.transcript.view-bubble .tline[data-h="unknown"]{justify-content:flex-start}
  .transcript.view-bubble .bub{max-width:82%;border-radius:12px;padding:7px 12px;font-size:13px;line-height:1.6}
  .transcript.view-bubble .tline[data-h="sup"] .bub{background:#eff6ff;border:1px solid #bfdbfe}
  .transcript.view-bubble .tline[data-h="sub"] .bub{background:#fdf2f8;border:1px solid #fbcfe8}
  .transcript.view-bubble .tline[data-h="other"] .bub,.transcript.view-bubble .tline[data-h="unknown"] .bub{background:#f8fafc;border:1px solid #e2e8f0}
  .transcript.view-bubble .line-speaker{display:block;font-size:11px;margin-bottom:2px}
  .transcript.view-bubble .tline[data-h="sup"] .line-speaker{color:#2563eb}
  .transcript.view-bubble .tline[data-h="sub"] .line-speaker{color:#db2777;text-align:right}
  .transcript.view-bubble .tline[data-h="other"] .line-speaker{color:#4b5563}
  .transcript.view-bubble .snd{color:#93c5fd;font-size:11px;margin-left:4px}
  .transcript.view-bubble .tline[data-h="sub"] .snd{color:#f0abbc}

  .transcript.view-plain .tline{margin:0;padding:5px 0;border-top:1px solid #f8fafc}
  .transcript.view-plain .tline:first-child{border-top:none}
  .transcript.view-plain .line-speaker{display:inline;font-size:13px;margin-right:6px}
  .transcript.view-plain .line-speaker[data-hier="sup"]{color:#2563eb}
  .transcript.view-plain .line-speaker[data-hier="sub"]{color:#db2777}
  .transcript.view-plain .line-speaker[data-hier="other"]{color:#475569}
  .transcript.view-plain .dia{font-size:13px;line-height:1.75;color:#334155}
  .transcript.view-plain .snd{color:#94a3b8;font-size:11px;margin-left:4px}

  .viewbtns{display:inline-flex;gap:4px;margin-left:14px;vertical-align:middle}
  .viewbtns button{border:1px solid #e2e8f0;background:#fff;color:#475569;border-radius:7px;padding:4px 11px;font-size:12px;font-weight:600;cursor:pointer}
  .viewbtns button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .meta-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}
  .meta-item{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:7px 10px}
  .meta-item .k{font-size:11px;color:var(--sub);font-weight:600;margin-bottom:2px}
  .meta-item .v{font-size:13px;color:#374151}
  .tag{display:inline-block;background:var(--tag);color:var(--accent);border-radius:6px;font-size:11px;padding:1px 7px;margin:2px 3px 0 0}
  .sensitive{color:#dc2626;font-weight:700}
  .hint{font-size:12px;color:var(--sub);margin-top:4px}
  @media(max-width:780px){nav.toc{display:none}.layout{padding:0}}
  /* 纠错弹窗 */
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
</style>
</head>
<body>
<header>
  <h1>Lの女性向音声剧 · Structured Catalog</h1>
  <div class="progress-wrap">
    <div class="prog">
      <span class="lab">结构化增强进度（已叠加角色/语气/音效/分析）</span>
      <span class="val" id="p1v"></span>
      <div class="bar"><i id="p1b"></i></div>
    </div>
    <div class="prog">
      <span class="lab">频道总进度（已转写 / 全 280 视频）</span>
      <span class="val" id="p2v"></span>
      <div class="bar"><i id="p2b"></i></div>
    </div>
    <div class="stats" id="stats"></div>
  </div>
  <input class="search" id="search" placeholder="搜索：标题 / 说话人 / 语气 / 场景 / 台词 / 题材 / 元素…（自动同义词归并）">
  <div class="filters" id="filters"></div>
  <div class="legend">
    <span class="grp"><b>身份：</b>
      <span class="it"><span class="sw" style="background:#2563eb"></span>上位者</span>
      <span class="it"><span class="sw" style="background:#db2777"></span>下位者</span>
      <span class="it"><span class="sw" style="background:#4b5563"></span>其他</span>
      <span class="it"><span class="sw" style="background:#f9fafb;border:1px dashed #cbd5e1"></span>未识别</span>
    </span>
    <span class="grp"><b>语气：</b>
      <span class="it"><span class="sw" style="background:#dc2626"></span>命令/严厉</span>
      <span class="it"><span class="sw" style="background:#ea580c"></span>请求/恳求</span>
      <span class="it"><span class="sw" style="background:#0d9488"></span>询问/疑惑</span>
      <span class="it"><span class="sw" style="background:#0ea5e9"></span>温柔/安抚</span>
      <span class="it"><span class="sw" style="background:#9ca3af"></span>平静/陈述</span>
      <span class="it"><span class="sw" style="background:#a855f7"></span>撒娇/亲密</span>
      <span class="it"><span class="sw" style="background:#6b21a8"></span>冷淡/嘲讽</span>
    </span>
    <span class="viewbtns" id="viewBtns">
      <b>台词视图：</b>
      <button data-view="script" class="on">剧本</button>
      <button data-view="bubble">气泡</button>
      <button data-view="plain">纯文本</button>
    </span>
    <button class="editbtn" id="editBtn">✎ 编辑台词</button>
    <button class="resetbtn" id="ovReset">清空纠错</button>
  </div>
</header>
<div class="layout">
  <nav class="toc" id="toc"></nav>
  <main id="main"></main>
</div>

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

function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
// 去掉频道前缀【Lの女性向音声】（数据中常见残形 "Lの女性向音声】"）
function cleanTitle(s){return (s||"").replace(/^【?Lの女性向音声[】\]]?\s*/, "");}

document.getElementById("p1v").textContent = ENRICHED + " / " + DONE + " 篇（" + Math.round(ENRICHED/DONE*100) + "%）· 精校 " + HAND + " · 自动 " + AUTO;
document.getElementById("p1b").style.width = (ENRICHED/DONE*100) + "%";
document.getElementById("p2v").textContent = DONE + " / " + TOTAL_CHANNEL +
  " 篇（" + Math.round(DONE/TOTAL_CHANNEL*100) + "%）· 余 " + (TOTAL_CHANNEL-DONE) + " 篇因 YouTube 年龄墙待补";
document.getElementById("p2b").style.width = (DONE/TOTAL_CHANNEL*100) + "%";
document.getElementById("stats").innerHTML =
  "台词行数 <b>"+DATA.reduce((a,r)=>a+r.lines.length,0)+"</b> · 行为节点 <b>"+
  DATA.reduce((a,r)=>a+r.behaviors.length,0)+"</b> · 精校 <b style='color:#16a34a'>"+HAND+"</b> · 自动 <b style='color:#b45309'>"+AUTO+"</b>";

/* ===== 身份层级 / 语气 颜色映射（可手动纠错） ===== */
// 身份层级判定标准（用户 2026-07-20 明确）：
//   上位 sup = 关系中支配/主导/供养/教导的一方：哥哥·主人·男友·老公·金主·老师……（蓝色的）
//   下位 sub = 从属/被宠/被照顾的一方：宝宝·小狗·宝贝·妹妹·少女·部下……（粉色的）
//   其它 other = 旁白/同事/电话音等非角色对话，或未被收录的称呼（灰色）
const HIER = {
  // —— 上位（sup）——
  "哥哥":"sup","哥":"sup","兄":"sup","兄长":"sup","お兄さん":"sup","主人":"sup","男友":"sup","老公":"sup","金主":"sup","老师":"sup",
  "彼":"sup","先辈":"sup","上司":"sup","先生":"sup","君":"sup","父":"sup","執事":"sup","执事":"sup","俺":"sup","夫君":"sup","爸爸":"sup",
  "爹地":"sup","爹":"sup","叔叔":"sup","继父":"sup","继兄":"sup","管家":"sup","医生":"sup","学长":"sup","殿下":"sup","陛下":"sup",
  "少爷":"sup","少主":"sup","公子":"sup","王爷":"sup","皇上":"sup","太子":"sup","影帝":"sup","总裁":"sup","老板":"sup","董事长":"sup",
  "警官":"sup","队长":"sup","教官":"sup","师父":"sup","师傅":"sup","长官":"sup","大人":"sup","他":"sup",
  // —— 下位（sub）——
  "弟":"sub","弟弟":"sub","妹":"sub","妹妹":"sub","少女":"sub","私":"sub","后辈":"sub","部下":"sub","仆":"sub","僕":"sub","子":"sub","女":"sub",
  "宝贝":"sub","宝宝":"sub","小狗":"sub","狗狗":"sub","你":"sub","您":"sub"
};
function hierOf(name){
  if(!name) return "unknown";
  if(HIER[name]==="sup") return "sup";
  if(HIER[name]==="sub") return "sub";
  return "other";
}
const TONE_COLOR = {
  "命令":"#dc2626","支配":"#dc2626","严厉":"#dc2626","叱":"#dc2626",
  "请求":"#ea580c","恳求":"#ea580c","哀求":"#ea580c",
  "询问":"#0d9488","疑惑":"#0d9488","疑问":"#0d9488",
  "温柔":"#0ea5e9","心疼":"#0ea5e9","安抚":"#0ea5e9","治愈":"#0ea5e9","溺爱":"#0ea5e9",
  "陈述":"#9ca3af","平静":"#9ca3af","平淡":"#9ca3af",
  "撒娇":"#a855f7","亲密":"#a855f7","宠溺":"#a855f7",
  "嘲讽":"#6b21a8","冷淡":"#6b21a8","戏谑":"#6b21a8","轻蔑":"#6b21a8"
};
function toneColor(t){
  if(!t) return "";
  for(const k in TONE_COLOR){ if(t.indexOf(k)>=0) return TONE_COLOR[k]; }
  return "#cbd5e1";
}

/* ===== 手动纠错覆盖（localStorage） ===== */
const OV_KEY = "vdr_overrides_v1";
let OV = {};
try { OV = JSON.parse(localStorage.getItem(OV_KEY) || "{}"); } catch(e){ OV = {}; }
function saveOV(){ try { localStorage.setItem(OV_KEY, JSON.stringify(OV)); } catch(e){} }
function getOV(vid, li){ return (OV[vid] && OV[vid][li]) || null; }

// 台词视图（剧本 / 气泡 / 纯文本），持久化到 localStorage
const LV_KEY = "vdr_lineview";
let LINE_VIEW = "script";
let CUR_LIST = [], CUR_KW = "";
try { const v = localStorage.getItem(LV_KEY); if(v==="script"||v==="bubble"||v==="plain") LINE_VIEW = v; } catch(e){}
function setLineView(v){
  if(v!=="script"&&v!=="bubble"&&v!=="plain") return;
  LINE_VIEW = v;
  try { localStorage.setItem(LV_KEY, v); } catch(e){}
  document.querySelectorAll("#viewBtns button[data-view]").forEach(b=>b.classList.toggle("on", b.dataset.view===v));
  render(CUR_LIST, CUR_KW);
}

function hl(text, kw){
  if(!kw) return esc(text);
  const i = text.toLowerCase().indexOf(kw.toLowerCase());
  if(i<0) return esc(text);
  return esc(text.slice(0,i)) + "<mark>" + esc(text.slice(i,i+kw.length)) + "</mark>" + esc(text.slice(i+kw.length));
}

function fmtLine(t, kw){
  t = (t||"").trim();
  if(!t) return "";
  t = t.replace(/\\s+/g, "，");
  if(!/[。！？!?]$/.test(t)) t += "。";
  return hl(t, kw);
}

function tagsHTML(arr, kw){
  return (arr||[]).map(t => '<span class="tag">'+hl(t,kw)+'</span>').join('');
}
function metaItem(k, v){
  return '<div class="meta-item"><div class="k">'+esc(k)+'</div><div class="v">'+v+'</div></div>';
}

// 台词行：按当前视图（剧本/气泡/纯文本）渲染
function lineHTML(r, li, l, kw){
  const ov = getOV(r.id, li);
  const speaker = (ov && ov.speaker!==undefined) ? ov.speaker : (l.speaker||"");
  const tone    = (ov && ov.tone!==undefined)    ? ov.tone    : (l.tone||"");
  const hier    = (ov && ov.hier) ? ov.hier : hierOf(speaker);
  const tc = toneColor(tone);
  const text = fmtLine(l.text, kw);
  const sound = (l.sound||[]).map(s=>'<span class="snd">'+hl(s,kw)+'</span>').join(' ');
  const snd = sound ? ' '+sound : '';
  const spkAttr = 'data-hier="'+hier+'" data-vid="'+r.id+'" data-li="'+li+'"';

  if(LINE_VIEW==="bubble"){
    const spk = speaker ? '<div class="spk line-speaker" '+spkAttr+' data-h="'+hier+'">'+hl(speaker,kw)+'</div>' : '';
    return '<div class="tline" data-h="'+hier+'"><div class="bub">'+spk+'<div class="dia">'+text+snd+'</div></div></div>';
  }
  if(LINE_VIEW==="plain"){
    const spk = speaker ? '<span class="spk line-speaker" '+spkAttr+' data-h="'+hier+'">'+hl(speaker,kw)+'</span>' : '';
    return '<div class="tline">'+spk+'<span class="dia">'+text+snd+'</span></div>';
  }
  // script（默认）
  const spk = speaker ? '<div class="spk line-speaker" '+spkAttr+' data-h="'+hier+'">'+hl(speaker,kw)+'</div>' : '<div class="spk line-speaker" '+spkAttr+'></div>';
  const diaStyle = tc ? ' style="border-left-color:'+tc+'"' : '';
  return '<div class="tline">'+spk+'<div class="dia"'+diaStyle+'>'+text+snd+'</div></div>';
}

// 篇级分析区（仅富集篇显示）
function metaHTML(r, kw){
  if(!r.enriched) return '';
  const parts = [];
  if(r.tone_summary){
    const cls = r.sensitive ? ' class="sensitive"' : '';
    parts.push(metaItem('语气总结', '<span'+cls+'>'+hl(r.tone_summary,kw)+'</span>'));
  }
  if((r.genre_tags||[]).length) parts.push(metaItem('题材 / 关系', tagsHTML(r.genre_tags,kw)));
  if(r.emotion_arc) parts.push(metaItem('情感弧线', hl(r.emotion_arc,kw)));
  if(r.intensity) parts.push(metaItem('强度', hl(r.intensity,kw)));
  if(r.listener_role) parts.push(metaItem('听者角色', hl(r.listener_role,kw)));
  if((r.signature_elements||[]).length) parts.push(metaItem('标志性元素', tagsHTML(r.signature_elements,kw)));
  if(!parts.length) return '';
  return '<div class="sec"><div class="t">内容分析</div><div class="meta-grid">'+parts.join('')+'</div></div>';
}

function cardHTML(r, kw){
  const badge = !r.enriched
    ? '<span class="badge base">基础版（增强中）</span>'
    : (r.tier === "auto"
        ? '<span class="badge auto">⚙ 自动增强（待精校）</span>'
        : '<span class="badge ok">✓ 精校增强</span>');
  const titleText = cleanTitle(r.title_zh || r.title);
  const beh = (r.behaviors||[]).map((b,i) =>
    '<li><span class="num">'+String(i+1)+'.</span><span>'+hl(b.desc,kw)+'</span></li>').join("");
  const lines = (r.lines||[]).map((l,i) => lineHTML(r, i, l, kw)).join("");
  const scene = r.scene ? '<div class="scene">'+hl(r.scene,kw)+'</div>' : '<div class="empty">（无场景描述）</div>';
  const behHTML = beh || '<div class="empty">（无行为节点）</div>';
  const lineHTML2 = lines || '<div class="empty">（无台词）</div>';
  const enhHint = r.enriched ? '' : '<div class="hint">本篇尚未叠加说话人/语气/音效/分析字段，完成增强后将自动更新。</div>';
  return '<section class="card" id="v'+r.id+'" data-id="'+r.id+'">'+
    '<h2>'+String(r.no).padStart(3,"0")+'. '+hl(titleText,kw)+badge+'</h2>'+
    '<div class="meta">时长 '+esc(r.duration)+' · <a href="'+esc(r.link)+'" target="_blank" rel="noopener">YouTube 原片 ↗</a></div>'+
    '<div class="sec"><div class="t">场景</div>'+scene+'</div>'+
    metaHTML(r, kw)+
    '<div class="sec"><div class="t">行为</div><ul class="beh">'+behHTML+'</ul></div>'+
    '<div class="sec"><div class="t">台词</div><div class="transcript view-'+LINE_VIEW+'">'+lineHTML2+'</div></div>'+
    enhHint+
    '</section>';
}

function render(list, kw){
  CUR_LIST = list; CUR_KW = kw;
  document.getElementById("main").innerHTML = list.map(r=>cardHTML(r,kw)).join("");
  document.getElementById("toc").innerHTML = list.map(r =>
    '<a href="#v'+r.id+'" data-id="'+r.id+'">'+String(r.no).padStart(3,"0")+'. '+esc(cleanTitle(r.title_zh||r.title))+'</a>').join("");
}

/* ===== A7 同义词归一 + B8 筛选器 ===== */
const SYNONYMS = {
  "哥哥": ["兄长","お兄さん","哥","兄"],
  "主人": ["主","主人公"],
  "管娇": ["打手心","OTK","巴掌","戒尺","管教","惩戒","spanking"],
  "调教": ["训练","规训"],
  "撒娇": ["娇","黏人","黏"],
  "宠溺": ["溺爱","宠","宠爱"],
  "温柔": ["温软","安抚","心疼","治愈"],
  "男友": ["老公","对象","先生"],
  "老师": ["师父","师傅"],
  "爸爸": ["爹地","父亲"],
  "宝宝": ["宝贝","小狗","狗狗"],
  "命令": ["支配","严厉","叱责"],
  "请求": ["恳求","哀求"],
  "询问": ["疑惑","疑问"],
  "冷淡": ["嘲讽","轻蔑","戏谑"]
};
function expandKw(kw){
  kw = (kw||"").trim().toLowerCase();
  if(!kw) return [];
  let arr = [kw];
  for(const k in SYNONYMS){
    const kl = k.toLowerCase();
    if(kw.indexOf(kl)>=0 || SYNONYMS[k].some(s=>kw.indexOf(s.toLowerCase())>=0))
      arr.push(...SYNONYMS[k].map(s=>s.toLowerCase()));
  }
  return [...new Set(arr)];
}
function kwHit(r, kws){
  if(!kws.length) return true;
  const low = s=>(s||"").toLowerCase();
  return kws.some(k =>
    low(cleanTitle(r.title)).indexOf(k)>=0 || low(cleanTitle(r.title_zh)).indexOf(k)>=0 || low(r.scene).indexOf(k)>=0 ||
    (r.behaviors||[]).some(b=>low(b.desc).indexOf(k)>=0) ||
    (r.lines||[]).some(l=>low(l.text).indexOf(k)>=0||low(l.speaker).indexOf(k)>=0||low(l.tone).indexOf(k)>=0||(l.sound||[]).some(s=>low(s).indexOf(k)>=0)) ||
    low(r.tone_summary).indexOf(k)>=0 || (r.genre_tags||[]).some(t=>low(t).indexOf(k)>=0) || low(r.listener_role).indexOf(k)>=0 || (r.signature_elements||[]).some(t=>low(t).indexOf(k)>=0)
  );
}
const FILTER = { hier:null, tone:null, genre:null, sensitive:null };
function filterHit(r){
  if(FILTER.hier){
    const sp = (r.lines&&r.lines[0]) ? r.lines[0].speaker : "";
    if(hierOf(sp)!==FILTER.hier) return false;
  }
  if(FILTER.tone){
    if(!(r.lines||[]).some(l=> (l.tone||"").indexOf(FILTER.tone)>=0)) return false;
  }
  if(FILTER.genre){
    if((r.genre_tags||[]).indexOf(FILTER.genre)<0) return false;
  }
  if(FILTER.sensitive==="y" && !r.sensitive) return false;
  if(FILTER.sensitive==="n" && r.sensitive) return false;
  return true;
}
function search(kw){
  const kws = expandKw(kw);
  const hit = DATA.filter(r => kwHit(r, kws) && filterHit(r));
  render(hit, kw);
}
const FILTER_DEFS = [
  { dim:"hier", label:"身份", opts:[["sup","上位者"],["sub","下位者"],["other","其他"]] },
  { dim:"tone", label:"语气", opts:[["命令","命令"],["请求","请求"],["询问","询问"],["温柔","温柔"],["撒娇","撒娇"],["责备","责备"],["宠溺","宠溺"],["平静","平静"]] },
  { dim:"genre", label:"题材", opts:[["古风","古风"],["校园/师生","校园/师生"],["主仆/调教","主仆/调教"],["职场","职场"],["医疗","医疗"],["家庭/长辈","家庭/长辈"],["现代情侣","现代情侣"],["治愈","治愈"]] },
  { dim:"sensitive", label:"敏感", opts:[["y","仅敏感"],["n","仅非敏感"]] },
];
function renderFilters(){
  const box = document.getElementById("filters");
  box.innerHTML = FILTER_DEFS.map(f =>
    '<span class="fgrp"><b>'+f.label+'：</b>'+
    '<span class="chip on" data-dim="'+f.dim+'" data-val="">全部</span>'+
    f.opts.map(o=>'<span class="chip" data-dim="'+f.dim+'" data-val="'+o[0]+'">'+o[1]+'</span>').join("")+
    '</span>'
  ).join("");
  box.querySelectorAll(".chip").forEach(ch=>{
    ch.addEventListener("click", ()=>{
      const dim=ch.dataset.dim, val=ch.dataset.val;
      FILTER[dim] = (FILTER[dim]===val && val!=="") ? null : val;
      const grp = ch.parentElement;
      grp.querySelectorAll(".chip").forEach(c=>c.classList.remove("on"));
      if(!FILTER[dim]){ grp.querySelector('[data-val=""]').classList.add("on"); }
      else { ch.classList.add("on"); }
      search(document.getElementById("search").value);
    });
  });
}
render(DATA, "");
renderFilters();
// 初始化台词视图按钮高亮（render 已用当前 LINE_VIEW 渲染）
document.querySelectorAll("#viewBtns button[data-view]").forEach(b=>b.classList.toggle("on", b.dataset.view===LINE_VIEW));
document.getElementById("viewBtns").addEventListener("click", e=>{
  const b = e.target.closest("button[data-view]"); if(!b) return;
  setLineView(b.dataset.view);
});
document.getElementById("search").addEventListener("input", e=>search(e.target.value));

document.getElementById("toc").addEventListener("click", e=>{
  const a = e.target.closest("a"); if(!a) return;
  e.preventDefault();
  const el = document.getElementById("v"+a.dataset.id);
  if(el) el.scrollIntoView({behavior:"smooth", block:"start"});
});

/* ===== 编辑模式 + 纠错弹窗 ===== */
let EDIT = false;
function toggleEdit(){
  EDIT = !EDIT;
  document.body.classList.toggle("edit", EDIT);
  const btn = document.getElementById("editBtn");
  btn.classList.toggle("on", EDIT);
  btn.textContent = EDIT ? "✎ 编辑模式：开" : "✎ 编辑台词";
}
function openEditor(vid, li, curSpeaker, curHier, curTone){
  const m = document.getElementById("ovModal");
  m.dataset.vid = vid; m.dataset.li = li;
  document.getElementById("ovSub").textContent = "视频 #"+vid+" · 第 "+(li+1)+" 句";
  document.getElementById("ovSpeaker").value = curSpeaker || "";
  const hv = curHier || hierOf(curSpeaker);
  const rad = document.querySelector('input[name=ovHier][value="'+hv+'"]');
  if(rad) rad.checked = true;
  document.getElementById("ovTone").value = curTone || "";
  m.style.display = "flex";
  document.getElementById("ovSpeaker").focus();
}
function closeEditor(){ document.getElementById("ovModal").style.display = "none"; }
function saveEditor(){
  const m = document.getElementById("ovModal");
  const vid = m.dataset.vid, li = +m.dataset.li;
  const speaker = document.getElementById("ovSpeaker").value.trim();
  const checked = document.querySelector('input[name=ovHier]:checked');
  const hier = checked ? checked.value : hierOf(speaker);
  const tone = document.getElementById("ovTone").value.trim();
  if(!OV[vid]) OV[vid] = {};
  OV[vid][li] = { speaker, hier, tone };
  saveOV();
  closeEditor();
  render(DATA, document.getElementById("search").value);
}

document.getElementById("editBtn").addEventListener("click", toggleEdit);
document.getElementById("ovSave").addEventListener("click", saveEditor);
document.getElementById("ovCancel").addEventListener("click", closeEditor);
document.getElementById("ovReset").addEventListener("click", ()=>{
  if(confirm("确定清空所有手动纠错？（仅清除本地覆盖，不影响原始数据）")){
    OV = {}; saveOV(); render(DATA, document.getElementById("search").value);
  }
});

document.getElementById("main").addEventListener("click", e=>{
  if(!EDIT) return;
  const t = e.target.closest(".line-speaker, .line-tone");
  if(!t) return;
  const vid = t.dataset.vid, li = +t.dataset.li;
  const rec = DATA.find(r=>r.id===vid);
  if(!rec) return;
  const l = rec.lines[li];
  const ov = getOV(vid, li);
  const speaker = (ov && ov.speaker!==undefined) ? ov.speaker : (l.speaker||"");
  const hier    = (ov && ov.hier) ? ov.hier : hierOf(speaker);
  const tone    = (ov && ov.tone!==undefined) ? ov.tone : (l.tone||"");
  openEditor(vid, li, speaker, hier, tone);
});
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
scripts = "".join(f'<script src="catalog_data/{fn}"></script>' for fn in part_files)
HTML = HTML.replace("__DATASCRIPTS__", scripts)
HTML = HTML.replace("__DATA__", "")
HTML = HTML.replace("__TOTAL_CHANNEL__", str(TOTAL_CHANNEL))

out = os.path.join(BASE, "mrlovewords9272_catalog.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)

print("data parts:", len(part_files), "| written:", out)

print("written:", out)
print("size MB: %.2f" % (os.path.getsize(out)/1024/1024))
print("records:", len(records), "| enriched:", enriched_count, "| lines:", line_count, "| behaviors:", behavior_count)
