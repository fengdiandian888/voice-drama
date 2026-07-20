#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich chunk_003: 复用原始台词文本，逐句标注 speaker/tone，并补全篇级分析。"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(BASE, "doc_data")
raw = json.load(open(os.path.join(DOC, "chunks", "chunk_003.json"), encoding="utf-8"))

# 每篇元数据
META = {
    "OIfTPNVF3kU": dict(
        speaker="哥哥", title_zh="别闹脾气了，来哥哥怀里~ (Don't be sulky! Come to my arms~)",
        tones=["责备","疑惑","责备","温柔","温柔","戏谑","戏谑"],
        tone_summary="从数落到门外道歉，再到坐腿上抱着温柔安抚，最后按墙假装绑起来调情和好——先凶后柔、带撒娇式管教。",
        genre_tags=["现代","情侣","日常","和好","宠溺"],
        emotion_arc="责备→道歉→温柔安抚→调情和好",
        intensity="中",
        listener_role="闹脾气、生闷气摔门、工作不顺的恋人（你/小兔）",
        signature_elements=["生闷气摔门","坐腿上抱","按墙假装绑起来调情"],
        sensitive=False,
    ),
    "RAYYlGdy8Zc": dict(
        speaker="哥哥", title_zh="就算翅膀折了，我也替你修补 (Even if your wings are broken, I'll repair them for you)",
        tones=["温柔","心疼","温柔","温柔","疑惑","宠溺","温柔","宠溺","温柔","心疼","温柔","心疼","温柔","温柔","宠溺","温柔","宠溺","心疼","平静","温柔","平静","温柔","温柔","宠溺","宠溺","宠溺","温柔","宠溺"],
        tone_summary="自伤后的极致温柔接纳与疗愈，保护欲满溢，从心疼、鼓励到宠溺再到深情告白。",
        genre_tags=["现代","情侣","治愈","自伤关怀","宠溺"],
        emotion_arc="心疼→安抚→鼓励→宠溺→深情告白",
        intensity="中（情感浓但无冲突）",
        listener_role="有自伤倾向、愧疚、抑郁的恋人（宝贝）",
        signature_elements=["上药","小拳头捶哥哥","养你一辈子","炒饭奶茶"],
        sensitive=False,
    ),
    "fkmxshfTCOs": dict(
        speaker="老师", title_zh="从今往后，你的身心都为我跳动 (From now on, your body and mind will beat for me)",
        tones=["平静","平静","平静","平静","命令","平静","平静","平静","询问","询问","平静","平静","戏谑","平静","平静","命令","命令","平静","命令","平静"],
        tone_summary="师生权力关系中的器物调教与服从训练，全程掌控、命令式，带 BDSM 暗示。",
        genre_tags=["校园","师生","调教","BDSM","权力关系"],
        emotion_arc="掌控→命令→调教→掌控",
        intensity="高（BDSM 暗示）",
        listener_role="被老师拿捏把柄、服从管教的学生（sub）",
        signature_elements=["检查/纸条","没收遥控器","消毒放入命令","调教"],
        sensitive=True,
    ),
    "iy6v3H6pWAk": dict(
        speaker="男友", title_zh="出差前一晚男友的温柔哄睡 (Gentle comfort of your boyfriend the night before his business trip)",
        tones=["温柔","温柔","宠溺","宠溺","宠溺","温柔"],
        tone_summary="出差前夜用睡前故事做分离脱敏，嘴硬心软、终是宠溺依偎，甜蜜不舍。",
        genre_tags=["现代","情侣","日常","睡前","分离焦虑","宠溺"],
        emotion_arc="温柔引导→心软宠溺→不舍告别",
        intensity="轻",
        listener_role="怕独处、撒娇黏人的恋人（宝宝/小兔子）",
        signature_elements=["小兔子小熊故事","分房睡训练","抱着小兔子睡","出差电话晚安"],
        sensitive=False,
    ),
    "Lhfh5p94pPY": dict(
        speaker="主人", title_zh="去夜店找男模？你真是想死！(Go to a nightclub? Still looking for male models! Oh, you really want to die!)",
        tones=["冷淡","命令","冷淡","平静","冷淡","平静","冷淡","责备","责备","命令","命令","命令","严厉","命令","严厉","命令","命令","严厉","命令","严厉","命令","命令","命令","严厉","平静","平静","温柔","平静","温柔","责备","冷淡","冷淡","冷淡","宠溺","心疼","心疼","责备","温柔","宠溺"],
        tone_summary="吃醋冷战后的惩罚与和解，先冷绝、再狠罚（扶墙挨戒尺/皮带）、终归于宠，掌控欲与保护欲交织。",
        genre_tags=["现代","情侣","主仆/调教","吃醋","惩罚","和好"],
        emotion_arc="冷淡决绝→严厉惩罚→心软安抚→宠溺和好",
        intensity="高",
        listener_role="吃醋闹脾气、故意引关注的恋人（你/sub）",
        signature_elements=["夜店男模","冷战分手","扶墙挨罚","换皮带","药膏陪睡"],
        sensitive=False,
    ),
}

out_videos = []
for v in raw["videos"]:
    vid = v["id"]
    m = META[vid]
    lines = []
    for (ts, text), tone in zip(v["lines"], m["tones"]):
        lines.append({"ts": ts, "text": text, "speaker": m["speaker"], "tone": tone, "sound": []})
    behaviors = [{"desc": b.get("desc", "")} for b in v.get("behaviors", [])]
    rec = {
        "id": vid,
        "title": v["title"],
        "title_zh": m["title_zh"],
        "duration": v.get("duration", ""),
        "link": v.get("link", ""),
        "lines": lines,
        "scene": v.get("scene", ""),
        "behaviors": behaviors,
        "tone_summary": m["tone_summary"],
        "genre_tags": m["genre_tags"],
        "emotion_arc": m["emotion_arc"],
        "intensity": m["intensity"],
        "listener_role": m["listener_role"],
        "signature_elements": m["signature_elements"],
        "sensitive": bool(m["sensitive"]),
    }
    out_videos.append(rec)

odir = os.path.join(DOC, "enriched")
os.makedirs(odir, exist_ok=True)
opath = os.path.join(odir, "chunk_003.json")
with open(opath, "w", encoding="utf-8") as f:
    json.dump(out_videos, f, ensure_ascii=False, indent=2)

# 校验行数一致
for v, o in zip(raw["videos"], out_videos):
    assert len(v["lines"]) == len(o["lines"]), (v["id"], len(v["lines"]), len(o["lines"]))
print("written:", opath)
print("videos:", len(out_videos))
for o in out_videos:
    print(" ", o["id"], "| lines:", len(o["lines"]), "| sensitive:", o["sensitive"])
