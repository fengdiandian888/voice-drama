#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the Lの系列音声剧 225-篇 结构化总册 (同步增强版).

数据源:
  - doc_data/videos_simp.json   (225篇基础台词, 已系统错别字校对)
  - doc_data/behavior_simp.json (场景 + 行为节点)
  - doc_data/enriched/chunk_*.json (已完成"一次性调整"的篇: 说话人/语气/音效/篇级分析)
合并规则: 每篇默认用基础数据; 若 enriched 中存在同 id, 则叠加新字段并标记 enriched.
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
            "sensitive": False,
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
<title>Lの女性向音声剧 · 结构化总册</title>
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
  .tline{margin:0 0 9px;padding:0;font-size:13.5px;color:#374151;text-align:justify;line-height:1.75}
  .tline:last-child{margin-bottom:0}
  .empty{color:var(--sub);font-style:italic}
  mark{background:#fde68a;border-radius:2px}
  .badge{display:inline-block;border-radius:999px;font-size:11px;padding:1px 9px;margin-left:8px;font-weight:600;vertical-align:middle}
  .badge.ok{background:#dcfce7;color:#16a34a}
  .badge.base{background:#f1f5f9;color:#94a3b8}
  .line-speaker{display:inline-block;background:#eef2ff;color:#4338ca;border-radius:4px;font-size:11px;padding:0 5px;margin-right:4px;font-weight:600}
  .line-tone{display:inline-block;background:#fef3c7;color:#b45309;border-radius:4px;font-size:11px;padding:0 5px;margin-right:4px;font-weight:600}
  .line-sound{display:inline-block;background:#fce7f3;color:#be185d;border-radius:4px;font-size:11px;padding:0 5px;margin-left:3px;font-weight:600}
  .meta-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}
  .meta-item{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:7px 10px}
  .meta-item .k{font-size:11px;color:var(--sub);font-weight:600;margin-bottom:2px}
  .meta-item .v{font-size:13px;color:#374151}
  .tag{display:inline-block;background:var(--tag);color:var(--accent);border-radius:6px;font-size:11px;padding:1px 7px;margin:2px 3px 0 0}
  .sensitive{color:#dc2626;font-weight:700}
  .hint{font-size:12px;color:var(--sub);margin-top:4px}
  @media(max-width:780px){nav.toc{display:none}.layout{padding:0}}
</style>
</head>
<body>
<header>
  <h1>Lの女性向音声剧 · 结构化总册</h1>
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
  <input class="search" id="search" placeholder="搜索：标题 / 说话人 / 语气 / 场景 / 台词 / 题材 / 元素…">
</header>
<div class="layout">
  <nav class="toc" id="toc"></nav>
  <main id="main"></main>
</div>

<script>
const DATA = __DATA__;
const TOTAL_CHANNEL = __TOTAL_CHANNEL__;
const DONE = DATA.length;
const ENRICHED = DATA.filter(r=>r.enriched).length;

function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

document.getElementById("p1v").textContent = ENRICHED + " / " + DONE + " 篇（" + Math.round(ENRICHED/DONE*100) + "%）· 余 " + (DONE-ENRICHED) + " 篇增强中";
document.getElementById("p1b").style.width = (ENRICHED/DONE*100) + "%";
document.getElementById("p2v").textContent = DONE + " / " + TOTAL_CHANNEL +
  " 篇（" + Math.round(DONE/TOTAL_CHANNEL*100) + "%）· 余 " + (TOTAL_CHANNEL-DONE) + " 篇因 YouTube 年龄墙待补";
document.getElementById("p2b").style.width = (DONE/TOTAL_CHANNEL*100) + "%";
document.getElementById("stats").innerHTML =
  "台词行数 <b>"+DATA.reduce((a,r)=>a+r.lines.length,0)+"</b> · 行为节点 <b>"+
  DATA.reduce((a,r)=>a+r.behaviors.length,0)+"</b> · 已增强 <b style='color:#16a34a'>"+ENRICHED+"</b>";

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

// 台词行：富集版叠加 说话人/语气/音效 标注；基础版仅文本
function lineHTML(l, kw){
  const pre = [];
  if(l.speaker) pre.push('<span class="line-speaker">'+hl(l.speaker,kw)+'</span>');
  if(l.tone) pre.push('<span class="line-tone">'+hl(l.tone,kw)+'</span>');
  const sound = (l.sound||[]).map(s=>'<span class="line-sound">'+hl(s,kw)+'</span>').join('');
  return '<p class="tline">'+pre.join('')+fmtLine(l.text, kw)+(sound?' '+sound:'')+'</p>';
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
  const badge = r.enriched
    ? '<span class="badge ok">✓ 已结构化增强</span>'
    : '<span class="badge base">基础版（增强中）</span>';
  const titleText = r.title_zh || r.title;
  const beh = (r.behaviors||[]).map((b,i) =>
    '<li><span class="num">'+String(i+1)+'.</span><span>'+hl(b.desc,kw)+'</span></li>').join("");
  const lines = (r.lines||[]).map(l => lineHTML(l, kw)).join("");
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
    '<div class="sec"><div class="t">台词</div><div class="transcript">'+lineHTML2+'</div></div>'+
    enhHint+
    '</section>';
}

function render(list, kw){
  document.getElementById("main").innerHTML = list.map(r=>cardHTML(r,kw)).join("");
  document.getElementById("toc").innerHTML = list.map(r =>
    '<a href="#v'+r.id+'" data-id="'+r.id+'">'+String(r.no).padStart(3,"0")+'. '+esc(r.title_zh||r.title)+'</a>').join("");
}

function search(kw){
  kw = (kw||"").trim();
  if(!kw){ render(DATA, ""); return; }
  const k = kw.toLowerCase();
  const hit = DATA.filter(r =>
    (r.title||"").toLowerCase().includes(k) ||
    (r.title_zh||"").toLowerCase().includes(k) ||
    (r.scene||"").toLowerCase().includes(k) ||
    (r.behaviors||[]).some(b => (b.desc||"").toLowerCase().includes(k)) ||
    (r.lines||[]).some(l => (l.text||"").toLowerCase().includes(k) ||
        (l.speaker||"").toLowerCase().includes(k) ||
        (l.tone||"").toLowerCase().includes(k) ||
        (l.sound||[]).some(s=>s.toLowerCase().includes(k))) ||
    (r.tone_summary||"").toLowerCase().includes(k) ||
    (r.genre_tags||[]).some(t=>t.toLowerCase().includes(k)) ||
    (r.listener_role||"").toLowerCase().includes(k) ||
    (r.signature_elements||[]).some(t=>t.toLowerCase().includes(k))
  );
  render(hit, kw);
}

render(DATA, "");
document.getElementById("search").addEventListener("input", e=>search(e.target.value));

document.getElementById("toc").addEventListener("click", e=>{
  const a = e.target.closest("a"); if(!a) return;
  e.preventDefault();
  const el = document.getElementById("v"+a.dataset.id);
  if(el) el.scrollIntoView({behavior:"smooth", block:"start"});
});
</script>
</body>
</html>
"""

HTML = HTML.replace("__DATA__", data_json)
HTML = HTML.replace("__TOTAL_CHANNEL__", str(TOTAL_CHANNEL))

out = os.path.join(BASE, "mrlovewords9272_总册.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)

print("written:", out)
print("size MB: %.2f" % (os.path.getsize(out)/1024/1024))
print("records:", len(records), "| enriched:", enriched_count, "| lines:", line_count, "| behaviors:", behavior_count)
