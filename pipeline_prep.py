# -*- coding: utf-8 -*-
"""准备阶段：合并最佳文本 -> 切 45 块(5篇/块) -> 写进度状态文件"""
import json, os

BASE = r"D:\WorkBuddy\2026-07-19-13-09-19"
DATA = os.path.join(BASE, "doc_data")

# 1) 载入系统词典版(全225已校正)
simp = json.load(open(os.path.join(DATA, "videos_simp.json"), encoding="utf-8"))
print("videos_simp:", len(simp))

# 2) 叠加已完成的 7 个 LLM 精校批(更准)
corr_files = ["batch_01.json","batch_02.json","batch_03.json","batch_04.json",
              "batch_05.json","batch_07.json","batch_12.json"]
overlay = {}
for f in corr_files:
    p = os.path.join(DATA, "corr_out", f)
    if os.path.exists(p):
        try:
            arr = json.load(open(p, encoding="utf-8"))
            for v in arr:
                if v.get("lines"):
                    overlay[v["id"]] = v["lines"]
        except Exception as e:
            print("skip", f, e)
print("LLM overlay videos:", len(overlay))

# 3) 载入已有场景/行为(供统一)
beh = {}
bp = os.path.join(DATA, "behavior_simp.json")
if os.path.exists(bp):
    try:
        beh = json.load(open(bp, encoding="utf-8"))
    except Exception:
        beh = {}

best = []
for v in simp:
    nv = {"id": v["id"], "title": v.get("title",""), "duration": v.get("duration",""),
          "link": v.get("link",""), "lines": v["lines"]}
    if v["id"] in overlay:
        nv["lines"] = overlay[v["id"]]
    if v["id"] in beh:
        nv["scene"] = beh[v["id"]].get("scene","")
        nv["behaviors"] = beh[v["id"]].get("behaviors",[])
    best.append(nv)

json.dump(best, open(os.path.join(DATA, "videos_best.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("videos_best:", len(best))

# 4) 切 45 块(5篇/块)
os.makedirs(os.path.join(DATA, "chunks"), exist_ok=True)
os.makedirs(os.path.join(DATA, "enriched"), exist_ok=True)
chunks = []
for i in range(0, len(best), 5):
    grp = best[i:i+5]
    idx = i // 5 + 1
    chunk = {"idx": idx, "videos": grp}
    chunks.append(chunk)
    json.dump(chunk, open(os.path.join(DATA, "chunks", f"chunk_{idx:03d}.json"),
                          "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("chunks:", len(chunks))

# 5) 写进度状态
from datetime import datetime
status = {
    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total": len(best),
    "total_chunks": len(chunks),
    "typo_llm_batches": 7,
    "chunks": [{
        "idx": c["idx"],
        "ids": [v["id"] for v in c["videos"]],
        "titles": [v["title"] for v in c["videos"]],
        "status": "待处理",
        "note": ""
    } for c in chunks]
}
json.dump(status, open(os.path.join(DATA, "progress_status.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("progress_status written")
