# -*- coding: utf-8 -*-
"""小鲸的视频理解：B 站链接 + 本地/相册视频。

原则：字幕优先，没字幕再本地 ASR；画面用 ffmpeg 抽关键帧，交给现有视觉模型。
不依赖新的聊天/视觉模型。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import subprocess
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# 国内网络优先走 HF 镜像，并关闭新版 Xet CAS（部分网络会失败）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")

try:
    import aiohttp
except Exception:  # pragma: no cover
    aiohttp = None

try:
    import yt_dlp
except Exception:  # pragma: no cover
    yt_dlp = None

try:
    import imageio_ffmpeg
except Exception:  # pragma: no cover
    imageio_ffmpeg = None

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover
    WhisperModel = None

try:
    import av
except Exception:  # pragma: no cover
    av = None

PLUGIN_DIR = Path(__file__).resolve().parent
DATA_DIR = PLUGIN_DIR / "data"
VIDEO_DIR = DATA_DIR / "video"
FRAME_DIR = VIDEO_DIR / "frames"
MODEL_DIR = DATA_DIR / "models"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
FRAME_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
BILI_HEADERS = {"User-Agent": UA, "Referer": "https://www.bilibili.com/"}
BVID_RE = re.compile(r"(BV[0-9A-Za-z]{10})")
AVID_RE = re.compile(r"av(\d+)", re.I)
BILI_HOST_RE = re.compile(r"(bilibili\.com|b23\.tv)", re.I)

_model_lock = threading.Lock()
_model_cache: dict[str, Any] = {}


@dataclass
class VideoResult:
    ok: bool
    source: str
    title: str = ""
    author: str = ""
    duration: float = 0.0
    platform: str = ""
    video_id: str = ""
    cover: str = ""
    desc: str = ""
    transcript: str = ""
    segments: list[dict] = field(default_factory=list)
    frames: list[str] = field(default_factory=list)
    error: str = ""
    cached: bool = False


def _ffmpeg() -> str:
    if not imageio_ffmpeg:
        return ""
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


def _run(cmd: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    kwargs: dict[str, Any] = {"capture_output": True, "timeout": timeout}
    if os.name == "nt":
        kwargs["creationflags"] = 0x08000000
    return subprocess.run(cmd, **kwargs)


def extract_bvid(text: str) -> str:
    m = BVID_RE.search(text or "")
    return m.group(1) if m else ""


def is_bilibili(text: str) -> bool:
    return bool(BILI_HOST_RE.search(text or "") or extract_bvid(text or ""))


async def _bili_json(url: str, params: dict | None = None, cookie: str = "") -> dict:
    if not aiohttp:
        return {}
    headers = dict(BILI_HEADERS)
    if cookie:
        headers["Cookie"] = cookie
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as s:
            async with s.get(url, params=params, headers=headers) as r:
                if r.status != 200:
                    return {}
                return await r.json(content_type=None)
    except Exception:
        return {}


async def resolve_bilibili(text: str, cookie: str = "") -> dict:
    """解析 BV/av/短链，返回 title/author/duration/cid/bvid。"""
    text = (text or "").strip()
    bvid = extract_bvid(text)
    if not bvid and "b23.tv" in text and aiohttp:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=12)) as s:
                async with s.get(text, headers=BILI_HEADERS, allow_redirects=True) as r:
                    final = str(r.url)
                    bvid = extract_bvid(final) or bvid
        except Exception:
            pass
    params: dict[str, Any] = {}
    if bvid:
        params["bvid"] = bvid
    else:
        m = AVID_RE.search(text)
        if m:
            params["aid"] = m.group(1)
    if not params:
        return {}
    j = await _bili_json("https://api.bilibili.com/x/web-interface/view", params, cookie)
    d = (j or {}).get("data") or {}
    if not d:
        return {}
    return {
        "bvid": d.get("bvid") or bvid,
        "aid": d.get("aid"),
        "cid": d.get("cid"),
        "title": d.get("title") or "",
        "author": ((d.get("owner") or {}).get("name") or ""),
        "duration": float(d.get("duration") or 0),
        "cover": d.get("pic") or "",
        "desc": d.get("desc") or "",
    }


async def bilibili_subtitle(meta: dict, cookie: str = "") -> tuple[str, list[dict]]:
    """取 B 站 CC/AI 字幕；没有就返回空。"""
    if not meta.get("bvid") or not meta.get("cid"):
        return "", []
    j = await _bili_json(
        "https://api.bilibili.com/x/player/v2",
        {"bvid": meta["bvid"], "cid": meta["cid"]},
        cookie,
    )
    subs = (((j or {}).get("data") or {}).get("subtitle") or {}).get("subtitles") or []
    if not subs:
        return "", []
    prefer = ("zh-Hans", "zh-CN", "ai-zh", "zh")
    chosen = None
    for lan in prefer:
        chosen = next((x for x in subs if str(x.get("lan") or "") == lan), None)
        if chosen:
            break
    chosen = chosen or subs[0]
    url = str(chosen.get("subtitle_url") or "")
    if url.startswith("//"):
        url = "https:" + url
    if not url:
        return "", []
    if not aiohttp:
        return "", []
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as s:
            async with s.get(url, headers=BILI_HEADERS) as r:
                if r.status != 200:
                    return "", []
                data = await r.json(content_type=None)
    except Exception:
        return "", []
    body = (data or {}).get("body") or []
    segments, lines = [], []
    for item in body:
        text = str(item.get("content") or "").strip()
        if not text:
            continue
        start = float(item.get("from") or 0)
        end = float(item.get("to") or start)
        segments.append({"start": start, "end": end, "text": text})
        lines.append(text)
    return "\n".join(lines), segments


def _ydl_opts(outtmpl: str, fmt: str, cookie: str = "") -> dict:
    headers = dict(BILI_HEADERS)
    if cookie:
        headers["Cookie"] = cookie
    return {
        "format": fmt,
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "socket_timeout": 25,
        "retries": 3,
        "http_headers": headers,
        "overwrites": True,
    }


def _download(url: str, out_dir: Path, fmt: str, cookie: str = "") -> str:
    if not yt_dlp:
        return ""
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with yt_dlp.YoutubeDL(_ydl_opts(str(out_dir / "media.%(ext)s"), fmt, cookie)) as ydl:
            info = ydl.extract_info(url, download=True)
        for item in (info.get("requested_downloads") or []):
            p = item.get("filepath") or item.get("_filename") or ""
            if p and Path(p).exists():
                return str(Path(p))
        for p in sorted(out_dir.glob("media.*")):
            if p.is_file():
                return str(p)
    except Exception:
        return ""
    return ""


def download_audio(url: str, out_dir: Path, cookie: str = "") -> str:
    return _download(url, out_dir, "bestaudio/best", cookie)


def download_video(url: str, out_dir: Path, cookie: str = "") -> str:
    p = _download(url, out_dir, "worst", cookie)
    if p:
        return p
    return _download(url, out_dir, "bestvideo[height<=480]/bestvideo", cookie)


def duration_of(path: str) -> float:
    try:
        if av:
            with av.open(path) as c:
                if c.duration:
                    return float(c.duration / 1_000_000)
    except Exception:
        pass
    try:
        ff = _ffmpeg()
        if ff:
            p = _run([ff, "-i", path], timeout=20)
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", p.stderr.decode("utf-8", "ignore"))
            if m:
                return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return 0.0


def extract_frames(path: str, out_dir: Path, count: int = 6) -> list[str]:
    ff = _ffmpeg()
    if not ff:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("frame_*.jpg"):
        p.unlink(missing_ok=True)
    dur = duration_of(path)
    count = max(1, min(12, int(count)))
    if dur > 0:
        times = [max(0.2, dur * (i + 0.5) / count) for i in range(count)]
    else:
        times = [1.0 + i * 2 for i in range(count)]
    frames = []
    for i, ts in enumerate(times):
        fp = out_dir / f"frame_{i:02d}.jpg"
        try:
            p = _run([
                ff, "-ss", f"{ts:.2f}", "-i", path, "-frames:v", "1",
                "-vf", "scale=640:-1", "-q:v", "3", "-y", str(fp),
            ], timeout=30)
            if fp.exists() and fp.stat().st_size > 2000:
                frames.append(str(fp))
        except Exception:
            continue
    return frames


def _get_model(model_size: str):
    if not WhisperModel:
        return None
    key = model_size or "small"
    if key in _model_cache:
        return _model_cache[key]
    with _model_lock:
        if key in _model_cache:
            return _model_cache[key]
        model = WhisperModel(
            key, device="cpu", compute_type="int8",
            download_root=str(MODEL_DIR),
        )
        _model_cache[key] = model
        return model


def transcribe(path: str, model_size: str = "small", language: str = "") -> tuple[str, list[dict]]:
    model = None
    for size in (model_size or "small", "base", "tiny"):
        try:
            model = _get_model(size)
            if model:
                break
        except Exception:
            model = None
    if not model:
        return "", []
    lang = language or None
    for use_vad in (True, False):
        try:
            segs, info = model.transcribe(
                path, language=lang, vad_filter=use_vad,
                beam_size=5, condition_on_previous_text=False,
            )
            items = []
            for s in segs:
                text = (s.text or "").strip()
                if not text:
                    continue
                items.append({"start": float(s.start), "end": float(s.end), "text": text})
            if items:
                return "\n".join(x["text"] for x in items), items
        except Exception:
            continue
    return "", []


def _cache_key_bili(meta: dict) -> str:
    return "bili_" + str(meta.get("bvid") or meta.get("aid") or "unknown")


def _cache_key_local(path: str) -> str:
    try:
        p = Path(path)
        raw = f"{p.resolve()}|{p.stat().st_size}|{int(p.stat().st_mtime)}"
    except Exception:
        raw = path
    return "local_" + hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:20]


def _load_cache(key: str, days: int) -> VideoResult | None:
    fp = VIDEO_DIR / f"{key}.json"
    try:
        if not fp.exists() or time.time() - fp.stat().st_mtime > days * 86400:
            return None
        data = json.loads(fp.read_text(encoding="utf-8"))
        frames = [x for x in (data.get("frames") or []) if Path(x).exists()]
        data["frames"] = frames
        data["cached"] = True
        return VideoResult(**data)
    except Exception:
        return None


def _save_cache(key: str, result: VideoResult) -> None:
    try:
        (VIDEO_DIR / f"{key}.json").write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
    except Exception:
        pass


async def process_bilibili(
    url: str, *, cookie: str = "", max_minutes: int = 30,
    max_frames: int = 6, asr_model: str = "small",
    asr_language: str = "", cache_days: int = 7,
) -> VideoResult:
    meta = await resolve_bilibili(url, cookie)
    if not meta:
        return VideoResult(False, url, error="B站视频信息解析失败（可能被风控或链接不完整）")
    key = _cache_key_bili(meta)
    cached = _load_cache(key, cache_days)
    if cached:
        return cached
    dur = float(meta.get("duration") or 0)
    if max_minutes and dur > max_minutes * 60:
        return VideoResult(
            False, url, title=meta.get("title", ""), author=meta.get("author", ""),
            duration=dur, platform="bilibili", video_id=meta.get("bvid", ""),
            cover=meta.get("cover", ""),
            error=f"视频 {dur/60:.0f} 分钟，超过当前上限 {max_minutes} 分钟",
        )
    transcript, segments = await bilibili_subtitle(meta, cookie)
    work = VIDEO_DIR / key
    work.mkdir(parents=True, exist_ok=True)
    if not transcript:
        audio = await asyncio.to_thread(download_audio, url, work / "audio", cookie)
        if audio:
            transcript, segments = await asyncio.to_thread(
                transcribe, audio, asr_model, asr_language,
            )
    video_path = await asyncio.to_thread(download_video, url, work / "video", cookie)
    frames: list[str] = []
    if video_path:
        frames = await asyncio.to_thread(extract_frames, video_path, FRAME_DIR / key, max_frames)
    result = VideoResult(
        True, url, title=meta.get("title", ""), author=meta.get("author", ""),
        duration=dur, platform="bilibili", video_id=meta.get("bvid", ""),
        cover=meta.get("cover", ""), desc=meta.get("desc", ""),
        transcript=transcript, segments=segments, frames=frames,
    )
    if not transcript and not frames:
        result.ok = False
        result.error = "没有拿到字幕、音频或画面"
    else:
        _save_cache(key, result)
    return result


async def process_local(
    path: str, *, max_minutes: int = 30, max_frames: int = 6,
    asr_model: str = "small", asr_language: str = "", cache_days: int = 7,
) -> VideoResult:
    p = Path(path)
    if not p.exists():
        return VideoResult(False, path, error="视频文件不存在")
    key = _cache_key_local(path)
    cached = _load_cache(key, cache_days)
    if cached:
        return cached
    dur = await asyncio.to_thread(duration_of, path)
    if max_minutes and dur > max_minutes * 60:
        return VideoResult(False, path, title=p.name, duration=dur, platform="local",
                           video_id=key, error=f"视频 {dur/60:.0f} 分钟，超过当前上限 {max_minutes} 分钟")
    frames = await asyncio.to_thread(extract_frames, path, FRAME_DIR / key, max_frames)
    transcript, segments = await asyncio.to_thread(transcribe, path, asr_model, asr_language)
    result = VideoResult(
        True, path, title=p.name, duration=dur, platform="local",
        video_id=key, transcript=transcript, segments=segments, frames=frames,
    )

    if not transcript and not frames:
        result.ok = False
        result.error = "没有拿到音频或画面"
    else:
        _save_cache(key, result)
    return result


async def process_video(
    source: str, *, local: bool = False, cookie: str = "",
    max_minutes: int = 30, max_frames: int = 6,
    asr_model: str = "small", asr_language: str = "",
    cache_days: int = 7,
) -> VideoResult:
    if local:
        return await process_local(
            source, max_minutes=max_minutes, max_frames=max_frames,
            asr_model=asr_model, asr_language=asr_language, cache_days=cache_days,
        )
    if is_bilibili(source):
        return await process_bilibili(
            source, cookie=cookie, max_minutes=max_minutes, max_frames=max_frames,
            asr_model=asr_model, asr_language=asr_language, cache_days=cache_days,
        )
    return VideoResult(False, source, error="目前只支持 B 站链接和本地/相册视频")


def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds or 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"
