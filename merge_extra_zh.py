#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 7 个 re-transcribe 的中译去重稿 (_transcripts_zh/<id>.txt) 合并进 extra_videos.json。

每个 zh 文件格式:  "[start-end] 文本"  一行一条。
解析为 lines:[{ts,text,speaker,tone,sound}]，并计算 duration（取最大 end）。
保留 extra_videos.json 中已有的 5IrMl5U2N_c，重复 id 不追加。
"""
import json, os, re, glob

BASE = os.path.dirname(os.path.abspath(__file__))
ZH = os.path.join(BASE, "output_mrlovewords9272", "_transcripts_zh")
EXTRA = os.path.join(BASE, "doc_data", "extra_videos.json")

# 7 个视频的元数据（题材标签取 render_master.GENRE_MAP 中的合法值）
META = {
    "BsUGt9TF_4g": dict(
        title_zh="妈妈与同公司心动之人的告白独白",
        genre_tags=["现代情侣", "独白"],
        listener_role="恋人 / 心动对象",
        tone_summary="（精校·中译去重）从妈妈电话到同公司心动之人的告白，回忆与幸福交织的独白。",
        intensity="中",
    ),
    "ETAEHAjsaMU": dict(
        title_zh="爸爸照顾生病宝宝的温柔哄睡",
        genre_tags=["治愈", "宠溺", "睡前", "家庭/长辈"],
        listener_role="被照顾的宝宝（下位）",
        tone_summary="（精校·中译去重）发烧生病被爸爸温柔照顾，推掉约会专门陪着的睡前哄睡。",
        intensity="中",
    ),
    "EqyXIVPTFqs": dict(
        title_zh="雨夜把流浪小猫领回家的故事",
        genre_tags=["宠物扮演", "治愈", "宠溺"],
        listener_role="被收养的小猫（下位）",
        tone_summary="（精校·中译去重）雨夜捡回受伤小野猫，洗净、喂奶、留客房，正式领养的温柔叙事。",
        intensity="中",
    ),
    "RZdsUpk0t3Q": dict(
        title_zh="雨夜依偎爸爸的安心哄睡",
        genre_tags=["治愈", "宠溺", "睡前", "家庭/长辈"],
        listener_role="被安抚的孩子 / 恋人（下位）",
        tone_summary="（精校·中译去重）雨声里呼唤爸爸、拥抱听心跳、倒数入睡的安心哄睡。",
        intensity="中",
    ),
    "dNWUEUdkEg8": dict(
        title_zh="给小猫处理伤口后的温软陪伴",
        genre_tags=["宠物扮演", "治愈", "医疗"],
        listener_role="被照顾的小猫（下位）",
        tone_summary="（精校·中译去重）处理胸口磕伤、消毒哄慰，之后柔软陪伴与领养回忆。",
        intensity="中",
    ),
    "ek2Qujkwq2o": dict(
        title_zh="居家办公陪小猫咪算账的甜宠日常",
        genre_tags=["现代情侣", "宠物扮演", "调情", "吃醋"],
        listener_role="被宠爱的小猫咪（下位）",
        tone_summary="（精校·中译去重）居家远程办公陪小猫咪，因挂电话吃醋被温柔算账的甜宠日常。",
        intensity="中",
    ),
    "wjLPlUcERaA": dict(
        title_zh="变成小鲸鱼的睡前童话与告白",
        genre_tags=["宠物扮演", "治愈", "睡前", "宠溺"],
        listener_role="被哄睡的宝贝（下位）",
        tone_summary="（精校·中译去重）变成小鲸鱼的梦境、海边童话与一句句“我爱你”的睡前告白。",
        intensity="中",
    ),
}

LINE_RE = re.compile(r"^\[([\d.]+-[\d.]+)\]\s*(.*)$")

def parse_zh(path):
    lines = []
    max_end = 0.0
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            m = LINE_RE.match(line)
            if not m:
                continue
            ts = m.group(1)
            text = m.group(2).strip()
            if not text:
                continue
            try:
                end = float(ts.split("-")[1])
                if end > max_end:
                    max_end = end
            except ValueError:
                pass
            lines.append({"ts": ts, "text": text, "speaker": "", "tone": "", "sound": []})
    dur = int(max_end // 60), int(round(max_end % 60))
    return lines, "%d:%02d" % dur

def main():
    extras = []
    if os.path.exists(EXTRA):
        extras = json.load(open(EXTRA, encoding="utf-8"))
    existing_ids = {e.get("id") for e in extras}

    added = 0
    for vid, meta in META.items():
        if vid in existing_ids:
            print("skip (already present):", vid)
            continue
        zp = os.path.join(ZH, vid + ".txt")
        if not os.path.exists(zp):
            print("MISSING zh file:", zp)
            continue
        lines, dur = parse_zh(zp)
        rec = {
            "id": vid,
            "title": vid,
            "title_zh": meta["title_zh"],
            "duration": dur,
            "link": "https://www.youtube.com/watch?v=" + vid,
            "enriched": True,
            "tier": "hand",
            "genre_tags": meta["genre_tags"],
            "intensity": meta["intensity"],
            "scene": "",
            "behaviors": [],
            "tone_summary": meta["tone_summary"],
            "emotion_arc": "",
            "listener_role": meta["listener_role"],
            "signature_elements": [],
            "sensitive": False,
            "lines": lines,
        }
        extras.append(rec)
        added += 1
        print("added:", vid, "lines=%d dur=%s" % (len(lines), dur))

    json.dump(extras, open(EXTRA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\nwritten extra_videos.json: total=%d added=%d" % (len(extras), added))

if __name__ == "__main__":
    main()
