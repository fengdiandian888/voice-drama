# -*- coding: utf-8 -*-
"""更新某块状态并重新渲染 progress.html。用法: python update_status.py <idx> <状态> [备注]"""
import json, os, sys
from datetime import datetime

BASE = r"D:\WorkBuddy\2026-07-19-13-09-19"
DATA = os.path.join(BASE, "doc_data")
S = json.load(open(os.path.join(DATA, "progress_status.json"), encoding="utf-8"))

idx = int(sys.argv[1])
status = sys.argv[2]
note = sys.argv[3] if len(sys.argv) > 3 else ""
found = False
for c in S["chunks"]:
    if c["idx"] == idx:
        c["status"] = status
        if note:
            c["note"] = note
        found = True
S["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json.dump(S, open(os.path.join(DATA, "progress_status.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(("updated chunk %d -> %s" % (idx, status)) if found else "chunk not found")
