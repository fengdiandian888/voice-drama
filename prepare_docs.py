#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 225 篇 .md 转写，提取 标题/视频ID/时长/链接/带时间戳台词。
输出 data/videos.json 与按批次生成的 data/batch_XX.txt 供 agent 读取重写。"""
import os, re, json, glob

SRC_DIR = "output_mrlovewords9272"
OUT_DIR = "doc_data"
BATCH = 25
os.makedirs(OUT_DIR, exist_ok=True)

ID_RE = re.compile(r"([A-Za-z0-9_-]{11})\.md$")
TS_RE = re.compile(r"^###\s*\[(\d{2}:\d{2}:\d{2})\]\s*$")
H1_RE = re.compile(r"^#\s+(.*)$")
META_RE = re.compile(r"^-\s*(\S+)\s*[:：]\s*(.*)$")

def parse_md(path):
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    title = None
    vid = None
    duration = None
    link = None
    m = ID_RE.search(os.path.basename(path))
    if m:
        vid = m.group(1)
    section = None
    cur_ts = None
    transcript = []  # list of (ts, text)
    buf = []
    def flush():
        if cur_ts is not None:
            t = " ".join(x.strip() for x in buf).strip()
            if t:
                transcript.append((cur_ts, t))
    for ln in lines:
        h1 = H1_RE.match(ln)
        if h1 and title is None:
            title = h1.group(1).strip()
            continue
        if ln.startswith("## "):
            flush()
            cur_ts = None
            section = ln[3:].strip()
            continue
        if ln.startswith("### "):
            flush()
            mt = TS_RE.match(ln)
            if section and "全文转写" in section and mt:
                cur_ts = mt.group(1)
                buf = []
            else:
                cur_ts = None
            continue
        if cur_ts is not None:
            buf.append(ln)
            continue
        # metadata
        if section is None or "元数据" in section:
            mm = META_RE.match(ln)
            if mm:
                k, v = mm.group(1), mm.group(2).strip()
                if "时长" in k: duration = v
                elif "链接" in k: link = v
    flush()
    if not link and vid:
        link = f"https://www.youtube.com/watch?v={vid}"
    return {
        "id": vid, "title": title or os.path.basename(path),
        "duration": duration, "link": link,
        "lines": transcript,
    }

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.md")))
videos = []
for f in files:
    try:
        v = parse_md(f)
        if v["lines"]:  # 只收有正文的
            videos.append(v)
    except Exception as e:
        print("parse fail", f, e)

print(f"parsed {len(videos)} videos with transcript")
json.dump(videos, open(os.path.join(OUT_DIR, "videos.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 生成批次文件
n = len(videos)
nb = (n + BATCH - 1) // BATCH
for bi in range(nb):
    chunk = videos[bi*BATCH:(bi+1)*BATCH]
    buf = []
    buf.append(f"本批次共 {len(chunk)} 篇。以下是每篇的【原始台词】（带时间戳），请据此重写【场景】与【行为】。\n")
    for idx, v in enumerate(chunk, 1):
        buf.append("="*70)
        buf.append(f"序号 {bi*BATCH+idx}  |  ID: {v['id']}")
        buf.append(f"标题: {v['title']}")
        buf.append(f"时长: {v['duration']}  |  链接: {v['link']}")
        buf.append("--- 原始台词（TRANSCRIPT，请保留原文字，不要改写）---")
        for ts, t in v["lines"]:
            buf.append(f"[{ts}] {t}")
        buf.append("")
    outp = os.path.join(OUT_DIR, f"batch_{bi+1:02d}.txt")
    open(outp, "w", encoding="utf-8").write("\n".join(buf))
    print("wrote", outp, "videos", len(chunk))
print(f"total batches: {nb}")
