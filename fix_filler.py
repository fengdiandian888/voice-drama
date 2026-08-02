#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并/折叠台词中的 filler 应答（嗯/啊/哦/唔/哼/呜/哈…），提升阅读流畅度。
作用于 doc_data/enriched/chunk_*.json 和 doc_data/extra_videos.json。

两阶段处理：
  阶段1（合并连续）：>=2 行连续、说话人相同、文本为纯 filler 的，合并为一行
    "（连续N声应答，已合并）"，保留首尾时间戳、说话人、语气、音效。
    单个孤立 filler 不在此阶段处理，留给阶段2。
  阶段2（折叠散落）：孤立 filler 若与上一行说话人相同，折入上一行末尾作软标记
    "（嗯）" / "（嗯·轻喘）"，既保留信息又不再独占一行。
    跨说话人的 filler（真实话轮）保留。

有信息量的短句（好/是/不要/疼/主人…）一律保留。
"""
import json, os, glob, re

BASE = os.path.dirname(os.path.abspath(__file__))
EN_DIR = os.path.join(BASE, "doc_data", "enriched")
EXTRA = os.path.join(BASE, "doc_data", "extra_videos.json")

FILLER_CHARS = set("嗯啊哦唔哼呜哈欸诶唉呼嘻嘿啧")
FILLER_DOUBLE = {"嗯嗯", "啊啊", "哦哦", "哈哈", "呼呼", "呜呜", "嘻嘻", "嘿嘿", "哼哼"}
FILLER_PAIR = {"哈啊", "啊哈", "嗯啊", "啊嗯", "唔嗯", "嗯哼", "哈嗯", "啊哦", "哦啊"}

STRIP_RE = re.compile(r"^[（(]?(.*?)[）)]?[。，！？、~～—－—…\s]*$")

def is_filler(text):
    if not text or not isinstance(text, str):
        return False
    m = STRIP_RE.match(text.strip())
    core = m.group(1).strip("。，！？、~～—－—…") if m else text.strip()
    if not core:
        return False
    if len(core) == 1 and core in FILLER_CHARS:
        return True
    if len(core) == 2:
        if core in FILLER_DOUBLE or core in FILLER_PAIR:
            return True
        if all(c in FILLER_CHARS for c in core):
            return True
    return False

def core_text(text):
    m = STRIP_RE.match(text.strip())
    return (m.group(1).strip("。，！？、~～—－—…") if m else text.strip()) or "嗯"

def ts_bounds(ts):
    if isinstance(ts, str) and "-" in ts:
        a, b = ts.split("-", 1)
        return a, b
    return ts, ts

def merge_run(run):
    first, last = run[0], run[-1]
    s, _ = ts_bounds(first.get("ts", ""))
    _, e = ts_bounds(last.get("ts", ""))
    core = core_text(first.get("text", ""))
    note = f"（连续{len(run)}声应答，已合并）"
    sounds = []
    for L in run:
        for s0 in (L.get("sound") or []):
            if s0 not in sounds:
                sounds.append(s0)
    return {
        "ts": f"{s}-{e}",
        "text": core + note,
        "speaker": first.get("speaker", ""),
        "tone": first.get("tone", ""),
        "sound": sounds,
    }

def fold_tag(line):
    core = core_text(line.get("text", ""))
    sounds = line.get("sound") or []
    if sounds:
        return f"（{core}·{'·'.join(sounds)}）"
    return f"（{core}）"

def fix_lines(lines):
    runs_merged = 0
    # 阶段1：仅合并长度>=2 的连续同说话人 filler
    pass1 = []
    run = []
    for line in lines:
        spk = line.get("speaker", "")
        if is_filler(line.get("text", "")) and (not run or run[-1].get("speaker", "") == spk):
            run.append(line)
        else:
            if len(run) >= 2:
                pass1.append(merge_run(run))
                runs_merged += 1
            elif len(run) == 1:
                pass1.append(run[0])  # 单个 filler 透传，留给阶段2
            run = []
            pass1.append(line)
    if len(run) >= 2:
        pass1.append(merge_run(run))
        runs_merged += 1
    elif len(run) == 1:
        pass1.append(run[0])

    # 阶段2：折叠与上一行同说话人的孤立 filler
    out = []
    folds = 0
    for line in pass1:
        spk = line.get("speaker", "")
        if is_filler(line.get("text", "")) and spk and out:
            prev = out[-1]
            if prev.get("speaker", "") == spk:
                prev["text"] = (prev.get("text", "") or "") + fold_tag(line)
                for s0 in (line.get("sound") or []):
                    if s0 not in (prev.get("sound") or []):
                        prev.setdefault("sound", []).append(s0)
                folds += 1
                continue
        out.append(line)
    return out, runs_merged, folds

def _sig(lines):
    return [(L.get("ts"), L.get("text"), L.get("speaker")) for L in lines]

def main():
    total_files = 0
    total_runs = 0
    total_folds = 0
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
            new_lines, runs, folds = fix_lines(lines)
            before, after = _sig(lines), _sig(new_lines)
            if before != after:
                total_runs += runs
                total_folds += folds
                total_before += len(lines)
                total_after += len(new_lines)
                vid["lines"] = new_lines
                changed = True
        if changed:
            json.dump(data, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            total_files += 1
            print("fixed:", os.path.basename(fp))

    print(f"\n汇总：修改 {total_files} 个文件")
    print(f"  合并连续 filler run（>=2）：{total_runs} 处")
    print(f"  折叠散落同说话人 filler：{total_folds} 行")
    print(f"  台词总行数 {total_before} → {total_after}（减少 {total_before - total_after} 行）")

if __name__ == "__main__":
    main()
