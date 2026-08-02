#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并台词中连续重复的行（同说话人 + 归一化文本完全相同），去除转写 artifact 造成的"复读"。
作用于 doc_data/enriched/chunk_*.json 与 doc_data/extra_videos.json。

规则：
- 仅合并「说话人相同 且 归一化文本完全相同」的连续行（归一化：去空白、去首尾标点）。
- 跨说话人的相同文本（真实对话轮次/回声）保留，不误删。
- run 长度 2：静默合并为 1 行（保留原文）。
- run 长度 >=3：合并并追加 "（重复N次，已合并）"。
- run 长度 >=5 且原文 <=4 字（卡段碎片）：替换为 "（约Ns 音频转写失真，已压缩）"。
- 合并保留首尾时间戳范围、说话人、语气、音效（去重合并）。
"""
import json, os, glob, re

BASE = os.path.dirname(os.path.abspath(__file__))
EN_DIR = os.path.join(BASE, "doc_data", "enriched")
EXTRA = os.path.join(BASE, "doc_data", "extra_videos.json")

PUNCT = "。，！？、~～—－—…,. "
STRIP_RE = re.compile(r"^[" + re.escape(PUNCT) + r"]*(.*?)[" + re.escape(PUNCT) + r"]*$")

def norm(t):
    if not t or not isinstance(t, str):
        return ""
    s = re.sub(r"\s+", "", t)
    m = STRIP_RE.match(s)
    core = m.group(1) if m else s
    return core.strip(PUNCT)

def ts_bounds(ts):
    if isinstance(ts, str) and "-" in ts:
        a, b = ts.split("-", 1)
        return a, b
    return ts, ts

def merge_run(run):
    first, last = run[0], run[-1]
    s, _ = ts_bounds(first.get("ts", ""))
    _, e = ts_bounds(last.get("ts", ""))
    text0 = (first.get("text", "") or "").strip()
    n = len(run)
    if n >= 5 and len(text0) <= 4:
        try:
            dur = round(float(e) - float(s), 1)
            label = f"（约{dur}秒音频转写失真，已压缩）"
        except Exception:
            label = "（音频转写失真，已压缩）"
        merged_text = label
    elif n >= 3:
        merged_text = text0 + f"（重复{len(run)}次，已合并）"
    else:
        merged_text = text0
    sounds = []
    for L in run:
        for s0 in (L.get("sound") or []):
            if s0 not in sounds:
                sounds.append(s0)
    return {
        "ts": f"{s}-{e}",
        "text": merged_text,
        "speaker": first.get("speaker", ""),
        "tone": first.get("tone", ""),
        "sound": sounds,
    }

def fix_lines(lines):
    out = []
    run = []
    for line in lines:
        cur = norm(line.get("text", ""))
        if run and cur and cur == norm(run[-1].get("text", "")) and line.get("speaker", "") == run[-1].get("speaker", ""):
            run.append(line)
        else:
            if len(run) >= 2:
                out.append(merge_run(run))
            elif run:
                out.append(run[0])
            run = [line]
    if len(run) >= 2:
        out.append(merge_run(run))
    elif run:
        out.append(run[0])
    return out

def _sig(lines):
    return [(L.get("ts"), L.get("text"), L.get("speaker")) for L in lines]

def main():
    total_files = 0
    total_runs = 0
    total_removed = 0
    total_before = 0
    total_after = 0

    targets = sorted(glob.glob(os.path.join(EN_DIR, "chunk_*.json"))) + [EXTRA]
    for fp in targets:
        data = json.load(open(fp, encoding="utf-8"))
        vids = data if isinstance(data, list) else [data]
        changed = False
        for vid in vids:
            lines = vid.get("lines", [])
            if not lines:
                continue
            new_lines = fix_lines(lines)
            if _sig(lines) != _sig(new_lines):
                removed = len(lines) - len(new_lines)
                # 统计合并的 run 数（粗略：reduced 行数）
                total_runs += max(0, removed)
                total_removed += removed
                total_before += len(lines)
                total_after += len(new_lines)
                vid["lines"] = new_lines
                changed = True
        if changed:
            json.dump(data, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            total_files += 1
            print("fixed:", os.path.basename(fp))

    print(f"\n汇总：修改 {total_files} 个文件")
    print(f"  合并重复 run：约 {total_runs} 处，减少 {total_removed} 行")
    print(f"  台词总行数 {total_before} → {total_after}")

if __name__ == "__main__":
    main()
