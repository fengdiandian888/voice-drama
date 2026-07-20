#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich chunk_004: 源 lines 为 [[ts,text]] 且文本未切句、无标点。
策略：① 按空格+标点把段切成句级；② speaker/篇级字段手写 META；
③ tone 用启发式逐句标注（可在总册页面手动精校）。"""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(BASE, "doc_data")
raw = json.load(open(os.path.join(DOC, "chunks", "chunk_004.json"), encoding="utf-8"))
videos = raw["videos"] if isinstance(raw, dict) else raw


def split_sentences(text):
    """口语无标点文本切句：先按空格分短句，再按标点细分。"""
    segs = []
    for chunk in text.split():
        chunk = chunk.strip(" ,，、。！？!?；;")
        if not chunk:
            continue
        for s in re.split(r"[。！？!?；;，、]+", chunk):
            s = s.strip()
            if s:
                segs.append(s)
    return segs


def guess_tone(t, speaker):
    """启发式语气标注（中文口语特征）。"""
    if re.search(r"[?？]|(吗|呢)\s*$", t):
        return "询问"
    if re.search(r"(不准|不许|别|快|起来|过来|出去|趴下|脱|给我|跪下|闭嘴|住口|自己)", t):
        return "命令"
    if re.search(r"(傻孩子|宝贝|宝宝|乖|嘛|呀|哼|亲|抱|揉)", t):
        return "撒娇"
    if re.search(r"(哭|累|疼|痛|心疼|苦|不容易|可怜|怕|冷)", t):
        return "温柔"
    if re.search(r"(胡闹|不成体统|怎么|又|罚|家法|和离|放肆)", t):
        return "责备"
    if re.search(r"(笑|喜欢|爱|乖|好本事|精进)", t):
        return "宠溺"
    return "平静"


META = {
    "7rD64SHCyg8": dict(
        speaker="哥哥",
        title_zh="你也为别人喝醉过吧？(Have you ever been drunk for anyone else?)",
        tone_summary="以'傻孩子'开场的心疼与质问，点破对方为别人醉、却不等自己哄的委屈，带点占有式的心疼。",
        genre_tags=["现代", "情侣", "心疼", "质问", "占有"],
        emotion_arc="心疼→质问→点破委屈",
        intensity="中",
        listener_role="曾为别人喝醉、让说话人吃醋心疼的恋人（你）",
        signature_elements=["傻孩子", "为别人醉", "不去哄你"],
        sensitive=False,
    ),
    "PEzc0ut3Nxg": dict(
        speaker="夫君",
        title_zh="我可不要那样的夫君！(I don't want a husband like that)",
        tone_summary="古风宅斗式训诫，夫君以家法、和离令威吓，先凶后带宠，掌控中透着吃味。",
        genre_tags=["古风", "夫妻", "训诫", "吃醋", "权力"],
        emotion_arc="训斥→威吓（家法/和离）→吃味宠溺",
        intensity="高",
        listener_role="耍赖、口出'和离令'、被家法伺候的夫人（你）",
        signature_elements=["家法", "屏风后", "和离令", "趴下"],
        sensitive=False,
    ),
    "txYVSIPAooM": dict(
        speaker="爸爸",
        title_zh="我知道你这个假期不开心 (I know you're not happy about this holiday)",
        tone_summary="以'爸爸'自称的宠溺安抚，承认生活苦、彼此是甜，温柔承接对方的不开心与脆弱。",
        genre_tags=["现代", "情侣", "安抚", "治愈", "宠溺"],
        emotion_arc="共情不开心→温柔承接→彼此是甜",
        intensity="轻",
        listener_role="假期不开心、脆弱需要被接住的恋人（你）",
        signature_elements=["爸爸称呼", "生活总是苦的", "那一点点甜"],
        sensitive=False,
    ),
    "UmDBYJm01Sc": dict(
        speaker="哥哥",
        title_zh="我永远是你躲风的港湾 (I will always be your refuge - Comfort after an argument)",
        tone_summary="吵架后的低声安慰，'吧''嗯'语气词多，从岔开话题到承认心疼，最终给承诺。",
        genre_tags=["现代", "情侣", "和好", "安慰", "治愈"],
        emotion_arc="岔开→承认心疼→承诺庇护",
        intensity="轻",
        listener_role="刚吵完架、在机场落单、需要被哄的恋人（你）",
        signature_elements=["吧", "好好睡一觉", "机场托行李", "永远是你港湾"],
        sensitive=False,
    ),
    "dkYwpy_MThI": dict(
        speaker="主人",
        title_zh="自己出来，你就是我的了 (If you come out by yourself, then you belong to me)",
        tone_summary="衣柜捉迷藏式的占有调情，先诱哄出来、再宣示归属，带控制欲与宠溺。",
        genre_tags=["现代", "情侣", "占有", "调情", "掌控"],
        emotion_arc="诱哄→宣示占有→控制式宠溺",
        intensity="中",
        listener_role="躲在衣柜里、被诱哄出来的恋人（你/sub）",
        signature_elements=["衣柜", "别玩了出来吧", "属于我", "吓到你了"],
        sensitive=False,
    ),
}

out_videos = []
for v in videos:
    vid = v["id"]
    if vid not in META:
        print("!! 缺少 META:", vid)
        continue
    m = META[vid]
    spk = m["speaker"]
    lines = []
    for item in v["lines"]:
        ts, text = item[0], item[1]
        for sent in split_sentences(text):
            lines.append({
                "ts": ts,
                "text": sent,
                "speaker": spk,
                "tone": guess_tone(sent, spk),
                "sound": [],
            })
    behaviors = [{"desc": b.get("desc", "")} for b in v.get("behaviors", [])]
    rec = {
        "id": vid,
        "title": v.get("title", ""),
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
opath = os.path.join(odir, "chunk_004.json")
with open(opath, "w", encoding="utf-8") as f:
    json.dump(out_videos, f, ensure_ascii=False, indent=2)

print("written:", opath)
print("videos:", len(out_videos))
for o in out_videos:
    print(f"  {o['id']} | speaker={o['lines'][0]['speaker'] if o['lines'] else '-'} | lines={len(o['lines'])} | sensitive={o['sensitive']}")
