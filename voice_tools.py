# -*- coding: utf-8 -*-
"""离线语音：用 Windows SAPI 生成 WAV，不依赖云 API。"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TTS_DIR = BASE_DIR / "data" / "cache" / "tts"
TTS_DIR.mkdir(parents=True, exist_ok=True)


def _clean(text: str) -> str:
    text = re.sub(r"\[\[[^\]]*\]\]", "", str(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:160]


def synthesize(text: str, voice: str = "Microsoft Huihui Desktop",
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
