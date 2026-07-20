#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量自动富集 chunk_005~045（205篇）：自动层，可由页面手动纠错精修。

源格式：{"idx":N,"videos":[...]}，lines=[[ts,text]] 无标点、段内多句未切。
处理：切句 + 上位词说话人识别 + 启发式语气 + 关键词题材标签 + 敏感标记 + 统计式篇级字段。
title_zh 留空（需读原文翻译，不臆造）；篇级总结为统计式并标注 (自动)。
"""
import json, os, re, glob
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(BASE, "doc_data")
ENRICHED = os.path.join(DOC, "enriched")

# 上位自称/称呼候选（只认上位，忽略下位称呼避免误判说话人）
SUP_WORDS = ["哥哥", "兄长", "主人", "老公", "金主", "老师", "男友", "夫君", "爸爸",
    "爹地", "先辈", "上司", "先生", "执事", "叔叔", "继父", "继兄", "管家", "医生",
    "学长", "殿下", "陛下", "少爷", "少主", "公子", "王爷", "皇上", "太子", "影帝",
    "总裁", "老板", "董事长", "警官", "队长", "教官", "师父", "师傅", "长官", "大人"]
# 注：不含单字"哥"（是"哥哥"子串会过度计数）；如需可在页面手动纠错

GENRE_KW = {
    "古风": ["夫君", "王爷", "殿下", "陛下", "皇上", "太子", "娘娘", "本王", "本宫",
             "公主", "将军", "朕", "阿哥", "朝堂", "府", "小姐", "姑娘", "和离", "家法", "妾"],
    "校园/师生": ["老师", "学长", "学姐", "同学", "作业", "考试", "教室", "教授",
                "同桌", "补课", "上课", "放学", "班主任"],
    "主仆/调教": ["主人", "调教", "项圈", "服从", "跪", "命令", "管教", "契约",
                "宠物", "归属", "规训", "狗狗", "小狗"],
    "职场": ["上司", "公司", "老板", "加班", "会议", "同事", "合同", "秘书",
            "董事长", "方案", "总裁", "下属"],
    "医疗": ["医生", "护士", "病人", "打针", "医院", "病房", "手术", "诊室"],
    "家庭/长辈": ["爸爸", "爹地", "叔叔", "继父", "继兄"],
    "现代情侣": ["男友", "老公", "宝贝", "亲爱的", "女朋友", "约会", "结婚"],
    "治愈": ["心疼", "抱抱", "乖", "没事", "陪你", "哄", "累了", "辛苦"],
}

SENSITIVE_KW = ["调教", "项圈", "戒尺", "皮带", "鞭", "捆", "绑", "惩戒", "打屁股",
                "情趣", "发情", "道具", "跪下", "惩罚", "禁欲", "囚", "锁链"]


def split_sentences(text):
    segs = []
    for chunk in str(text).split():
        chunk = chunk.strip(" ,，、。！？!?；;")
        if not chunk:
            continue
        for s in re.split(r"[。！？!?；;，、]+", chunk):
            s = s.strip()
            if s:
                segs.append(s)
    return segs


def guess_tone(t):
    if re.search(r"[?？]|(吗|呢)$", t):
        return "询问"
    if re.search(r"(不准|不许|别|快点|起来|过来|出去|趴下|脱|给我|跪下|闭嘴|住口|听话|不可以)", t):
        return "命令"
    if re.search(r"(傻孩子|宝贝|宝宝|乖|嘛|呀|哼|亲亲|抱抱|揉揉|好不好|要抱)", t):
        return "撒娇"
    if re.search(r"(哭|累|疼|痛|心疼|苦|不容易|可怜|怕|冷|辛苦|没事|陪你|别怕)", t):
        return "温柔"
    if re.search(r"(胡闹|不成体统|怎么又|罚|家法|和离|放肆|说过多少次|又|竟然|居然)", t):
        return "责备"
    if re.search(r"(笑|喜欢|爱你|乖乖|真乖|听话就|奖励|我的)", t):
        return "宠溺"
    return "平静"


def detect_speaker(full_text):
    c = Counter()
    for w in SUP_WORDS:
        n = full_text.count(w)
        if n:
            c[w] = n
    if not c:
        return "他", False  # 默认上位（女性向多为男性上位独白），低置信
    return c.most_common(1)[0][0], True


def detect_genres(full_text):
    hits = []
    for g, kws in GENRE_KW.items():
        if any(k in full_text for k in kws):
            hits.append(g)
    if not hits:
        hits = ["现代情侣"]
    # 现代情侣兜底，但若已有古风/校园等更具体标签则去掉泛化的"现代情侣"
    if len(hits) > 1 and "现代情侣" in hits:
        hits = [h for h in hits if h != "现代情侣"]
    return hits[:4]


def detect_sensitive(full_text):
    hit = [k for k in SENSITIVE_KW if k in full_text]
    return (len(hit) >= 2), hit


def summarize(tones, speaker, genres):
    c = Counter(tones)
    top = [t for t, _ in c.most_common(3)]
    top_str = "、".join(top) if top else "平静"
    return f"（自动）{speaker}视角独白，语气以{top_str}为主，题材偏{genres[0] if genres else '现代情侣'}。"


def emotion_arc(tones):
    if not tones:
        return "（自动）平静"
    n = len(tones)
    a = Counter(tones[:max(1, n // 3)]).most_common(1)[0][0]
    b = Counter(tones[n // 3:2 * n // 3] or tones).most_common(1)[0][0]
    c = Counter(tones[2 * n // 3:] or tones).most_common(1)[0][0]
    seq = [a, b, c]
    dedup = [seq[0]] + [x for i, x in enumerate(seq[1:], 1) if x != seq[i - 1]]
    return "（自动）" + "→".join(dedup)


def intensity_of(tones, sensitive):
    c = Counter(tones)
    hard = c.get("命令", 0) + c.get("责备", 0)
    if sensitive:
        return "高（含敏感/控制元素）"
    if hard >= max(3, len(tones) * 0.25):
        return "中偏高"
    if c.get("温柔", 0) + c.get("撒娇", 0) >= len(tones) * 0.4:
        return "轻"
    return "中"


def enrich_video(v):
    lines_src = v.get("lines", [])
    full_text = " ".join(str(x[1]) for x in lines_src)
    speaker, conf = detect_speaker(full_text)
    genres = detect_genres(full_text)
    sensitive, skw = detect_sensitive(full_text)

    lines = []
    tones = []
    for item in lines_src:
        ts, text = item[0], item[1]
        for sent in split_sentences(text):
            tone = guess_tone(sent)
            tones.append(tone)
            lines.append({"ts": ts, "text": sent, "speaker": speaker,
                          "tone": tone, "sound": []})

    behaviors = [{"desc": b.get("desc", "")} for b in v.get("behaviors", [])]
    return {
        "id": v["id"],
        "title": v.get("title", ""),
        "title_zh": "",  # 自动层不臆造翻译，留空由 render 回退英文原标题
        "duration": v.get("duration", ""),
        "link": v.get("link", ""),
        "lines": lines,
        "scene": v.get("scene", ""),
        "behaviors": behaviors,
        "tone_summary": summarize(tones, speaker, genres),
        "genre_tags": genres + (["敏感"] if sensitive else []),
        "emotion_arc": emotion_arc(tones),
        "intensity": intensity_of(tones, sensitive),
        "listener_role": f"（自动）被{speaker}倾诉/照顾/管教的一方（你）",
        "signature_elements": skw[:5],
        "sensitive": bool(sensitive),
        "tier": "auto",
        "speaker_confident": bool(conf),
    }


def main():
    os.makedirs(ENRICHED, exist_ok=True)
    done = 0
    stat_speaker = Counter()
    low_conf = []
    for f in sorted(glob.glob(os.path.join(DOC, "chunks", "chunk_*.json"))):
        n = int(re.search(r"chunk_(\d+)", f).group(1))
        if n <= 4:
            continue  # 001-004 已手写精校，跳过
        raw = json.load(open(f, encoding="utf-8"))
        videos = raw["videos"] if isinstance(raw, dict) else raw
        out = []
        for v in videos:
            rec = enrich_video(v)
            out.append(rec)
            sp = rec["lines"][0]["speaker"] if rec["lines"] else "-"
            stat_speaker[sp] += 1
            if not rec["speaker_confident"]:
                low_conf.append(rec["id"])
        opath = os.path.join(ENRICHED, f"chunk_{n:03d}.json")
        with open(opath, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
        done += len(out)
        print(f"  chunk_{n:03d}: {len(out)} 篇")
    print(f"\n自动富集完成：{done} 篇（chunk_005~045）")
    print("说话人分布:", dict(stat_speaker.most_common()))
    print(f"低置信(默认'他')篇数: {len(low_conf)} -> {low_conf}")


if __name__ == "__main__":
    main()
