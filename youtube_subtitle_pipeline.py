#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 频道/播放列表 → 本地中文转写 → 字幕 + 文本稿 + 结构化文档 管道

依赖: yt-dlp, faster-whisper (自动调用本机 GPU, 无 GPU 则 CPU 回退)
全程本地运行，无需调用任何付费 API。需要能访问 YouTube 的网络(VPN)。

用法:
  # 整频道转写(默认断点续跑, 自动用 GPU)
  python youtube_subtitle_pipeline.py --url "https://www.youtube.com/@某频道/videos" --output ./output

  # 强制指定设备
  python youtube_subtitle_pipeline.py --url "<URL>" --device cuda
  python youtube_subtitle_pipeline.py --url "<URL>" --device cpu

  # GPU 显存小(如 2GB)时用小模型, 否则 medium 可能装不下
  python youtube_subtitle_pipeline.py --url "<URL>" --device cuda --model small

  # 先小批量试跑前 2 条(只列+下载+转写 2 条)
  python youtube_subtitle_pipeline.py --url "<URL>" --limit 2

  # 只列出视频,不下载(看频道规模)
  python youtube_subtitle_pipeline.py --url "<URL>" --dry-run

  # 更准但更慢更大: large-v3
  python youtube_subtitle_pipeline.py --url "<URL>" --model large-v3

  # 自动检测语言(中英混杂时)
  python youtube_subtitle_pipeline.py --url "<URL>" --lang auto
"""
import argparse
import json
import os
import re
import sys
import shutil
import subprocess
import datetime
import time
from pathlib import Path

# ---------------- 默认配置 ----------------
DEFAULT_MODEL = "medium"          # 中文平衡: medium | 更准: large-v3 (更慢更占内存)
DEFAULT_LANG  = "zh"              # 中文: zh | 自动检测: auto
WHISPER_THREADS = max(4, min(8, os.cpu_count() or 4))  # CPU 并行线程数
COMPUTE_TYPE = "int8"            # CPU 用 int8 最快; 有 GPU 时改 float16
PARAGRAPH_GAP = 2.5              # 段落切分间隔(秒): 相邻语段间隔大于此值则另起一段
MANIFEST_NAME = "manifest.json"  # 进度/续跑记录
LOG_NAME = "pipeline.log"


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    _log_file.write(line + "\n")
    _log_file.flush()


_log_file = open(os.devnull, "w", encoding="utf-8")


def sanitize(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return (name[:120] or "untitled").strip()


def ensure_ffmpeg():
    """确保 ffmpeg 在 PATH 中(兜底 WinGet 安装位置)。"""
    p = shutil.which("ffmpeg")
    if p:
        return p
    cand_dir = r"C:/Users/Administrator/AppData/Local/Microsoft/WinGet/Links"
    cand = os.path.join(cand_dir, "ffmpeg.exe")
    if os.path.exists(cand):
        os.environ["PATH"] = cand_dir + os.pathsep + os.environ.get("PATH", "")
        return cand
    return None


def ensure_node():
    """确保 node 在 PATH 中(yt-dlp 下载需要 JS 运行时解析格式)，返回 node 路径或 None。"""
    p = shutil.which("node")
    if p:
        return p
    # 管理的 node 安装位置
    cand_dir = r"C:/Users/Administrator/.workbuddy/binaries/node/versions/22.22.2"
    cand = os.path.join(cand_dir, "node.exe")
    if os.path.exists(cand):
        os.environ["PATH"] = cand_dir + os.pathsep + os.environ.get("PATH", "")
        return cand
    return None


def ensure_ytdlp():
    """定位 yt-dlp 可执行文件(优先 PATH，否则 venv Scripts 目录)。"""
    p = shutil.which("yt-dlp")
    if p:
        return p
    cand = os.path.join(os.path.dirname(sys.executable), "yt-dlp.exe")
    if os.path.exists(cand):
        return cand
    return "yt-dlp"


def setup_cuda_path():
    """把 pip 安装的 nvidia CUDA 运行时 DLL 目录加入 PATH。

    pip 装的 nvidia-* 包把 cublas64_12.dll 等放在
    site-packages/nvidia/<pkg>/bin/ 下，不在系统 PATH 中。
    ctranslate2 的 CUDA 后端在真正调用 GPU 编码时才会按需加载这些 DLL，
    若不在 PATH 则报 'Library cublas64_12.dll is not found or cannot be loaded'。
    这里在启动时一次性把所有 nvidia/*/bin 加入 PATH，保证 GPU 推理可用。
    """
    import site
    site_dirs = []
    try:
        site_dirs = site.getsitepackages()
    except Exception:
        site_dirs = []
    nvidia_dirs = []
    for sp in site_dirs:
        cand = os.path.join(sp, "nvidia")
        if os.path.isdir(cand):
            nvidia_dirs.append(cand)
    if not nvidia_dirs:
        # 兜底: 沿 sys.path 找含 nvidia 包的目录
        for p in sys.path:
            cand = os.path.join(p, "nvidia")
            if os.path.isdir(cand):
                nvidia_dirs.append(cand)
    if not nvidia_dirs:
        return []
    cur = os.environ.get("PATH", "").split(os.pathsep)
    added = []
    for nv in nvidia_dirs:
        for name in sorted(os.listdir(nv)):
            bin_dir = os.path.join(nv, name, "bin")
            if os.path.isdir(bin_dir) and bin_dir not in cur:
                added.append(bin_dir)
    if added:
        os.environ["PATH"] = os.pathsep.join(added) + os.pathsep + os.environ.get("PATH", "")
        log(f"[cuda] 已把 {len(added)} 个 nvidia DLL 目录加入 PATH")
    return added


def load_manifest(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def fmt_hms(s: float) -> str:
    s = int(round(s))
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def fmt_srt(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def fmt_vtt(s: float) -> str:
    return fmt_srt(s).replace(",", ".")


def list_videos(url: str, limit: int, sleep: int, js_arg: list) -> list:
    """用 yt-dlp 扁平列出频道/播放列表下所有视频(不下载)。"""
    cmd = [
        ensure_ytdlp(),
        "--flat-playlist",
        "--skip-download",
        "-J",
        "--sleep-interval", str(sleep),
    ]
    cmd += js_arg
    cmd += [url]
    log(f"列出视频中: {url}")
    data = None
    for attempt in range(1, 4):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        except subprocess.TimeoutExpired:
            log(f"  [列出超时] 第 {attempt} 次，60s 后重试")
            if attempt < 3:
                time.sleep(60)
            continue
        if out.returncode == 0 and out.stdout.strip():
            try:
                data = json.loads(out.stdout)
                break
            except Exception:
                log(f"  [解析失败] 第 {attempt} 次，重试中…")
        else:
            log(f"  [列出失败] 第 {attempt} 次: {((out.stderr or out.stdout) or '无输出')[-500:]}")
        if attempt < 3:
            log("  YouTube 可能触发了反爬/限流，60s 后重试…")
            time.sleep(60)
    if data is None:
        log("yt-dlp 多次列出失败，放弃本次列出。")
        return []
    # 频道/播放列表返回 entries; 单视频则返回单个对象本身
    if isinstance(data, dict) and data.get("entries"):
        entries = data["entries"]
        channel_default = data.get("channel") or data.get("uploader") or ""
    elif isinstance(data, dict) and data.get("id"):
        entries = [data]
        channel_default = data.get("channel") or data.get("uploader") or ""
    elif isinstance(data, list):
        entries = data
        channel_default = ""
    else:
        entries = []
        channel_default = ""
    videos = []
    for e in entries:
        if not e:
            continue
        vid = e.get("id")
        if not vid:
            continue
        videos.append({
            "id": vid,
            "title": e.get("title") or vid,
            "url": e.get("url") or f"https://www.youtube.com/watch?v={vid}",
            "duration": e.get("duration") or 0,
            "channel": (e.get("channel") or channel_default
                        or e.get("uploader") or ""),
        })
    if limit and limit > 0:
        videos = videos[:limit]
    return videos


def download_audio(video: dict, audio_dir: Path, sleep: int, js_arg: list, max_retry: int = 3) -> str | None:
    """下载最佳音轨为 m4a，返回文件路径。YouTube 偶发限流/反爬会瞬时失败，
    这里做 max_retry 次重试(每次间隔退避)，让临时性封锁自动恢复。"""
    outtmpl = str(audio_dir / "%(id)s.%(ext)s")
    cmd = [
        ensure_ytdlp(),
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "-x", "--audio-format", "m4a",
        "--no-playlist",
        "--sleep-interval", str(sleep),
        "-o", outtmpl,
    ]
    cmd += js_arg
    cmd += [video["url"]]
    last_err = ""
    for attempt in range(1, max_retry + 1):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            last_err = "timeout"
            log(f"  [下载超时] {video['title']} (第{attempt}次)")
        else:
            if r.returncode == 0:
                matches = list(audio_dir.glob(f"{video['id']}.*"))
                matches = [m for m in matches if m.suffix.lower() in (".m4a", ".webm", ".opus", ".aac", ".mp3")]
                if matches:
                    return str(matches[0])
                last_err = "no-file"
                log(f"  [未找到音频文件] {video['title']} (第{attempt}次)")
            else:
                last_err = (r.stderr or r.stdout)[-800:]
                log(f"  [下载失败] {video['title']} (第{attempt}次)\n{last_err}")
        if attempt < max_retry:
            log(f"  YouTube 可能限流，45s 后重试…")
            time.sleep(45)
    return None


def to_wav_16k(src: str, ffmpeg: str) -> str:
    """转成 16k 单声道 wav 供 whisper 读取(临时文件)。"""
    wav = src + ".16k.wav"
    cmd = [
        ffmpeg, "-y", "-i", src,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav,
    ]
    subprocess.run(cmd, capture_output=True, timeout=300)
    return wav


def resolve_device(device: str) -> str:
    """auto → 有 CUDA 用 cuda，否则 cpu。"""
    if device in ("cpu", "cuda"):
        return device
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    return "cpu"


def transcribe(wav_path: str, model_size: str, lang: str, vad: bool = False, device: str = "auto"):
    """返回 (segments, info)。segments: [{start,end,text}]"""
    from faster_whisper import WhisperModel
    dev = resolve_device(device)
    # CUDA 下优先 float16(快), 老卡(如 Maxwell sm_50)不支持则回退 float32
    cands = ["float16", "float32"] if dev == "cuda" else [COMPUTE_TYPE]
    threads = 1 if dev == "cuda" else WHISPER_THREADS
    model = None
    last_err = None
    for ct in cands:
        try:
            model = WhisperModel(model_size, device=dev,
                                 compute_type=ct, cpu_threads=threads)
            compute_type = ct
            break
        except ValueError as e:
            last_err = e
            continue
    if model is None:
        raise last_err or RuntimeError("无法初始化 whisper 模型")
    log(f"  [转写] device={dev} compute={compute_type} model={model_size}")
    kwargs = dict(beam_size=5)
    if vad:
        kwargs["vad_filter"] = True
        kwargs["vad_parameters"] = dict(min_silence_duration_ms=500)
    if lang and lang != "auto":
        kwargs["language"] = lang
    segments_iter, info = model.transcribe(wav_path, **kwargs)
    segs = []
    for s in segments_iter:
        segs.append({"start": s.start, "end": s.end, "text": s.text.strip()})
    return segs, info


def build_paragraphs(segs: list) -> list:
    """按时间间隔切分段落。每段: {start, end, text}"""
    paras = []
    cur = None
    for s in segs:
        if cur is None:
            cur = {"start": s["start"], "end": s["end"], "text": s["text"]}
        else:
            gap = s["start"] - cur["end"]
            if gap > PARAGRAPH_GAP:
                paras.append(cur)
                cur = {"start": s["start"], "end": s["end"], "text": s["text"]}
            else:
                cur["end"] = s["end"]
                cur["text"] += " " + s["text"]
    if cur:
        paras.append(cur)
    return paras


def write_srt(segs: list, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{fmt_srt(s['start'])} --> {fmt_srt(s['end'])}\n{s['text']}\n\n")


def write_vtt(segs: list, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{fmt_vtt(s['start'])} --> {fmt_vtt(s['end'])}\n{s['text']}\n\n")


def write_txt(paras: list, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for p in paras:
            f.write(p["text"] + "\n\n")


def write_md(video, segs, paras, info, model_size, lang, path: Path):
    total = max((s["end"] for s in segs), default=0)
    speech = sum((s["end"] - s["start"]) for s in segs)
    speech_ratio = (speech / total * 100) if total else 0
    lines = []
    lines.append(f"# {video['title']}\n")
    lines.append("## 元数据")
    lines.append(f"- 频道: {video.get('channel') or '未知'}")
    lines.append(f"- 时长: {fmt_hms(total)}")
    lines.append(f"- 语音占比: {speech_ratio:.1f}%（静音已过滤）")
    lines.append(f"- 转写语言: {'自动检测' if lang == 'auto' else '中文'}")
    lines.append(f"- 模型: {model_size} ({COMPUTE_TYPE})")
    lines.append(f"- 链接: {video['url']}")
    lines.append(f"- 处理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 时间轴目录")
    for i, p in enumerate(paras, 1):
        snippet = p["text"][:40].replace("\n", " ")
        lines.append(f"{i}. `[{fmt_hms(p['start'])}]` {snippet}…")
    lines.append("")
    lines.append("## 全文转写")
    for p in paras:
        lines.append(f"### [{fmt_hms(p['start'])}]")
        lines.append(p["text"])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def process_video(video, args, audio_dir, out_dir, ffmpeg, manifest, js_arg):
    vid = video["id"]
    if vid in manifest and manifest[vid].get("status") == "ok" and not args.no_resume:
        # 检查产物是否还在
        rec = manifest[vid]
        if rec.get("outputs", {}).get("srt") and Path(rec["outputs"]["srt"]).exists():
            log(f"  [跳过·已存在] {video['title']}")
            return
    log(f"▶ 处理: {video['title']}  ({fmt_hms(video.get('duration') or 0)})")
    audio = download_audio(video, audio_dir, args.sleep, js_arg)
    if not audio:
        manifest[vid] = {"status": "download_failed", "title": video["title"]}
        return
    wav = to_wav_16k(audio, ffmpeg)
    try:
        segs, info = transcribe(wav, args.model, args.lang, vad=args.vad, device=args.device)
    except Exception as e:
        log(f"  [转写异常] {video['title']}: {e}")
        manifest[vid] = {"status": "transcribe_failed", "title": video["title"]}
        return
    finally:
        if os.path.exists(wav):
            try:
                os.remove(wav)
            except OSError:
                pass
    if not segs:
        log(f"  [无语音内容] {video['title']}")
        manifest[vid] = {"status": "empty", "title": video["title"]}
        return
    base = sanitize(video["title"])
    # 防止重名覆盖: 加 id 后缀
    safe_base = f"{base}__{vid}"
    srt_p = out_dir / (safe_base + ".srt")
    vtt_p = out_dir / (safe_base + ".vtt")
    txt_p = out_dir / (safe_base + ".txt")
    md_p = out_dir / (safe_base + ".md")
    paras = build_paragraphs(segs)
    write_srt(segs, srt_p)
    write_vtt(segs, vtt_p)
    write_txt(paras, txt_p)
    write_md(video, segs, paras, info, args.model, args.lang, md_p)
    if not args.keep_audio and os.path.exists(audio):
        try:
            os.remove(audio)
        except OSError:
            pass
    manifest[vid] = {
        "status": "ok",
        "title": video["title"],
        "url": video["url"],
        "channel": video.get("channel"),
        "segments": len(segs),
        "processed_at": datetime.datetime.now().isoformat(),
        "outputs": {
            "srt": str(srt_p), "vtt": str(vtt_p),
            "txt": str(txt_p), "md": str(md_p),
        },
    }
    log(f"  [完成] 段落 {len(paras)} · 字幕 {len(segs)} 条 → {safe_base}")


def main():
    global _log_file
    ap = argparse.ArgumentParser(description="YouTube → 本地中文转写 → 字幕/文本/文档")
    ap.add_argument("--url", required=True, help="频道/播放列表/单视频 URL")
    ap.add_argument("--output", default="./output", help="输出目录 (默认 ./output)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"whisper 模型 (默认 {DEFAULT_MODEL})")
    ap.add_argument("--lang", default=DEFAULT_LANG, help="语言: zh / auto (默认 zh)")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 条(试跑用)")
    ap.add_argument("--sleep", type=int, default=2, help="yt-dlp 请求间隔秒(默认 2)")
    ap.add_argument("--cookies", default=None,
                    help="YouTube cookies 文件路径(如 cookies.txt)，用于绕过年龄验证/登录限制。"
                         "从浏览器(Chrome/Edge)用插件导出 cookies.txt 后传入")
    ap.add_argument("--dry-run", action="store_true", help="只列出视频,不下载")
    ap.add_argument("--no-resume", action="store_true", help="忽略已处理记录,强制重跑")
    ap.add_argument("--keep-audio", action="store_true", help="保留下载的音频文件")
    ap.add_argument("--vad", action="store_true",
                    help="启用语音活动检测(VAD)过滤静音，可提升成片整洁度；"
                         "若误判导致字幕为空请去掉此开关")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"],
                    help="推理设备: auto(有GPU用cuda否则cpu) / cpu / cuda (默认 auto)")
    args = ap.parse_args()

    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = out_dir / "_audio"
    audio_dir.mkdir(exist_ok=True)
    _log_file = open(out_dir / LOG_NAME, "a", encoding="utf-8")

    # 写入自身 PID，供监控页准确判断进程是否真在运行(避免靠日志时间误判)
    pid_path = out_dir / "pipeline.pid"
    try:
        pid_path.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    setup_cuda_path()  # 确保 nvidia CUDA 运行时 DLL 在 PATH 中(GPU 推理必需)
    ffmpeg = ensure_ffmpeg()
    if not ffmpeg:
        log("未找到 ffmpeg，请先安装 ffmpeg 并加入 PATH。")
        return
    node = ensure_node()
    js_arg = ["--js-runtimes", "node"] if node else []
    if args.cookies:
        if not os.path.exists(args.cookies):
            log(f"[警告] --cookies 指定文件不存在: {args.cookies}，将忽略")
        else:
            js_arg += ["--cookies", args.cookies]
            log(f"已启用 cookies(绕过年龄验证): {args.cookies}")
    if node:
        log(f"node(JS运行时): {node}")
    else:
        log("未找到 node，yt-dlp 可能无法解析 YouTube 格式(下载或失败)。建议安装 Node.js。")
    log(f"ffmpeg: {ffmpeg}")
    log(f"配置: model={args.model} lang={args.lang} device={args.device} threads={WHISPER_THREADS} compute={COMPUTE_TYPE}")

    videos = list_videos(args.url, args.limit, args.sleep, js_arg)
    log(f"共发现 {len(videos)} 个视频。")
    if args.dry_run:
        for i, v in enumerate(videos, 1):
            log(f"  {i:>3}. [{fmt_hms(v.get('duration') or 0)}] {v['title']}")
        log("dry-run 结束。去掉 --dry-run 开始处理。")
        return

    manifest_path = out_dir / MANIFEST_NAME
    manifest = load_manifest(manifest_path)
    if args.no_resume:
        manifest = {}

    ok = fail = 0
    for v in videos:
        before = manifest.get(v["id"], {}).get("status")
        process_video(v, args, audio_dir, out_dir, ffmpeg, manifest, js_arg)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        st = manifest[v["id"]].get("status")
        if st == "ok":
            ok += 1
        elif st in ("download_failed", "transcribe_failed", "empty"):
            fail += 1
    log(f"==== 完成: 成功 {ok} · 失败/跳过 {fail} · 总计 {len(videos)} ====")
    log(f"产物目录: {out_dir}")

    # 正常结束，清理 PID 文件
    try:
        if pid_path.exists():
            pid_path.unlink()
    except Exception:
        pass


if __name__ == "__main__":
    main()
