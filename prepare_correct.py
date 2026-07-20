#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Split 225 transcripts into proofreading batches (15 videos each)."""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(BASE, "doc_data")
SRC = os.path.join(DOC, "videos_simp.json")

vids = json.load(open(SRC, encoding="utf-8"))
print("records:", len(vids))

BATCH = 15
corr_in = os.path.join(DOC, "corr_in")
corr_out = os.path.join(DOC, "corr_out")
os.makedirs(corr_in, exist_ok=True)
os.makedirs(corr_out, exist_ok=True)

batches = [vids[i:i+BATCH] for i in range(0, len(vids), BATCH)]
for bi, batch in enumerate(batches, 1):
    tag = f"batch_{bi:02d}"
    payload = [{
        "id": v["id"],
        "title": v.get("title", ""),
        "lines": v.get("lines", []),   # [["ts","text"], ...]
    } for v in batch]
    with open(os.path.join(corr_in, f"{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

print("batches:", len(batches))
print("corr_in ->", corr_in)
print("corr_out ->", corr_out)
