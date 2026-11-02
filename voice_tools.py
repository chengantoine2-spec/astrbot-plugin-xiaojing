# -*- coding: utf-8 -*-
"""离线语音：用 Windows SAPI 生成 WAV，不依赖云 API。"""

from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TTS_DIR = BASE_DIR / "data" / "cache" / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)


def _prune() -> None:
    try:
        old = sorted(TTS_DIR.glob("tts_*.*"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
        for item in old[40:]:
            item.unlink(missing_ok=True)
    except Exception:
        pass


def _clean(text: str) -> str:
    text = re.sub(r"\[\[[^\]]*\]\]", "", str(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:160]


def synthesize_sapi(text: str, voice: str = "Microsoft Huihui Desktop",
                    rate: int = -1, timeout: int = 30) -> Path | None:
    """生成 WAV；失败返回 None。"""
    text = _clean(text)
    if not text:
        return None
    stamp = int(time.time() * 1000)
    wav = TTS_DIR / f"tts_{stamp}.wav"
    txt = TTS_DIR / f"tts_{stamp}.txt"
    try:
        txt.write_text(text, encoding="utf-8")
        def q(value: str) -> str:
            return "'" + str(value).replace("'", "''") + "'"
        ps = (
            "Add-Type -AssemblyName System.Speech\n"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
            f"$s.SelectVoice({q(voice)})\n"
            f"$s.Rate = {int(rate)}\n"
            "$s.Volume = 100\n"
            f"$s.SetOutputToWaveFile({q(str(wav))})\n"
            f"$s.Speak([IO.File]::ReadAllText({q(str(txt))}, [Text.Encoding]::UTF8))\n"
            "$s.Dispose()\n"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            capture_output=True,
            timeout=max(5, int(timeout)),
            creationflags=0x08000000,
        )
        if wav.exists() and wav.stat().st_size > 1000:
            try:
                old = sorted(TTS_DIR.glob("tts_*.wav"),
                             key=lambda p: p.stat().st_mtime, reverse=True)
                for item in old[30:]:
                    item.unlink(missing_ok=True)
            except Exception:
                pass
            return wav
    except Exception:
        pass
    finally:
        try:
            txt.unlink(missing_ok=True)
        except Exception:
            pass
    return None


def synthesize_openai(text: str, cfg: dict | None = None,
                      timeout: int = 60) -> Path | None:
    """OpenAI 兼容的 /audio/speech；适配 vLLM-Omni Qwen3-TTS 本地服务。"""
    text = _clean(text)
    cfg = cfg or {}
    if not text:
        return None
    base = str(cfg.get("tts_base") or "").rstrip("/")
    if not base:
        return None
    key = str(cfg.get("tts_key") or "")
    model = str(cfg.get("tts_model") or "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
    voice = str(cfg.get("tts_api_voice") or "Vivian")
    payload = {
        "model": model,
        "voice": voice,
        "input": text,
        "response_format": "wav",
    }
    if cfg.get("tts_language"):
        payload["language"] = str(cfg.get("tts_language"))
    if cfg.get("tts_instruct"):
        payload["instruct"] = str(cfg.get("tts_instruct"))
    req = urllib.request.Request(
        base + "/audio/speech",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": "Bearer " + key} if key else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(10, int(timeout))) as r:
            data = r.read()
    except Exception:
        return None
    if not data or len(data) < 1000:
        return None
    ext = ".wav" if data[:4] == b"RIFF" else ".mp3"
    out = TTS_DIR / f"tts_{int(time.time() * 1000)}{ext}"
    try:
        out.write_bytes(data)
        _prune()
        return out
    except Exception:
        return None


def synthesize_auto(text: str, cfg: dict | None = None) -> Path | None:
    """按配置选 TTS：sapi 默认；openai 兼容服务失败可回退 SAPI。"""
    cfg = cfg or {}
    provider = str(cfg.get("tts_provider") or "sapi").lower()
    if provider in ("openai", "qwen", "vllm", "custom"):
        fp = synthesize_openai(text, cfg)
        if fp:
            return fp
        if not cfg.get("tts_fallback_sapi", True):
            return None
    voice = str(cfg.get("tts_sapi_voice") or "Microsoft Huihui Desktop")
    return synthesize_sapi(text, voice=voice)


# 兼容旧调用
synthesize = synthesize_sapi
