#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""繁体 -> 简体：场景 / 行为 / 台词 全部转写，存为 *_simp.json（原文件保留）。"""
import json, os
from opencc import OpenCC

BASE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(BASE, "doc_data")
c = OpenCC('t2s')  # Traditional to Simplified

def t(s):
    return c.convert(s) if isinstance(s, str) else s

vids = json.load(open(os.path.join(DOC, "videos.json"), encoding="utf-8"))
beh = json.load(open(os.path.join(DOC, "behavior_merged.json"), encoding="utf-8"))

for x in vids:
    x["title"] = t(x.get("title", ""))
    x["lines"] = [[ln[0], t(ln[1])] for ln in x.get("lines", [])]

for k, vv in beh.items():
    vv["scene"] = t(vv.get("scene", ""))
    for b in vv.get("behaviors", []):
        b["desc"] = t(b.get("desc", ""))

json.dump(vids, open(os.path.join(DOC, "videos_simp.json"), "w", encoding="utf-8"),
          ensure_ascii=False)
json.dump(beh, open(os.path.join(DOC, "behavior_simp.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

print("converted:", len(vids), "videos |", len(beh), "behaviors")
# quick sample
print("sample title:", vids[0]["title"])
print("sample line :", vids[0]["lines"][1])
print("sample scene:", beh[vids[0]["id"]]["scene"][:80])
