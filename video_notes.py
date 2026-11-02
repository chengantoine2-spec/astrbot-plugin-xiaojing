# -*- coding: utf-8 -*-
"""视频笔记：把看过的视频摘要、时间戳要点和来源留在本地。"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VIDEO_DIR = DATA_DIR / "video"
NOTES_PATH = VIDEO_DIR / "notes.json"


def _load() -> dict:
    try:
        data = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("notes", [])
            return data
    except Exception:
        pass
    return {"notes": []}


def _save(data: dict) -> None:
    try:
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        data["notes"] = (data.get("notes") or [])[-300:]
        data["updated"] = int(time.time())
        NOTES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    except Exception:
        pass


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "")).lower()[:200]


def _note_key(result) -> str:
    source = str(getattr(result, "source", "") or "").strip()
    title = str(getattr(result, "title", "") or "").strip()
    video_id = str(getattr(result, "video_id", "") or "").strip()
    raw = video_id or f"{source}|{title}"
    return "vn" + hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:16]


def _summary_lines(summary: str) -> list[str]:
    lines = []
    for line in str(summary or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("原链接", "来源：", "链接：")):
            continue
        text = re.sub(r"^[\s\-*•·]+", "", line)
        text = re.sub(r"^\d+[.、)]\s*", "", text).strip()
        if text:
            lines.append(text)
    return lines


def save(result, summary: str) -> dict:
    """保存或更新一条视频笔记；同一视频重复看不会堆重复条目。"""
    text = str(summary or "").strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text:
        return {}
    source = str(getattr(result, "source", "") or "").strip()
    title = str(getattr(result, "title", "") or "").strip() or source
    key = _note_key(result)
    data = _load()
    now = int(time.time())
    note = {
        "id": key,
        "title": title[:160],
        "author": str(getattr(result, "author", "") or "")[:80],
        "source": source[:500],
        "platform": str(getattr(result, "platform", "") or "")[:40],
        "duration": int(float(getattr(result, "duration", 0) or 0)),
        "summary": text[:4000],
        "points": _summary_lines(text)[:12],
        "transcript_chars": len(str(getattr(result, "transcript", "") or "")),
        "frames": len(getattr(result, "frames", []) or []),
        "created": now,
        "updated": now,
    }
    notes = data.get("notes") or []
    old = next((x for x in notes if x.get("id") == key), None)
    if old:
        note["created"] = int(old.get("created") or now)
        notes[notes.index(old)] = note
    else:
        notes.append(note)
    data["notes"] = notes
    _save(data)
    return note


def list_notes(limit: int = 10, keyword: str = "") -> list[dict]:
    notes = _load().get("notes", [])
    if keyword:
        q = str(keyword).lower()
        notes = [x for x in notes
                 if q in str(x.get("title") or "").lower()
                 or q in str(x.get("summary") or "").lower()
                 or q in str(x.get("source") or "").lower()
                 or q in str(x.get("author") or "").lower()]
    return sorted(notes, key=lambda x: x.get("updated", 0), reverse=True)[:max(1, int(limit))]


def remove_notes(keyword: str) -> int:
    q = str(keyword or "").strip().lower()
    if not q:
        return 0
    data = _load()
    old = data.get("notes", [])
    keep = [x for x in old
            if q not in str(x.get("title") or "").lower()
            and q not in str(x.get("summary") or "").lower()
            and q not in str(x.get("source") or "").lower()]
    data["notes"] = keep
    _save(data)
    return len(old) - len(keep)


def format_notes(limit: int = 10, keyword: str = "") -> str:
    all_notes = _load().get("notes", [])
    items = list_notes(limit, keyword)
    if not items:
        return "还没有视频笔记。发我 B 站链接或视频，我看完会记下来。"
    lines = [f"视频笔记 {len(all_notes)} 条，最近 {len(items)} 条："]
    for x in items:
        mins = int(x.get("duration") or 0) // 60
        lines.append(f"- 《{x.get('title') or '未命名'}》{f'（{mins} 分钟）' if mins else ''}")
        if x.get("author"):
            lines.append(f"  UP：{x.get('author')}")
        points = x.get("points") or []
        for p in points[:4]:
            lines.append(f"  · {p[:120]}")
        if not points:
            lines.append(f"  · {str(x.get('summary') or '')[:120]}")
        if x.get("source"):
            lines.append(f"  来源：{x.get('source')}")
    return "\n".join(lines)[:1800]


def facts_from_summary(summary: str, source: str, title: str = "", limit: int = 6) -> list[dict]:
    """把总结里的要点转成世界记忆事实；只有公开 http 来源才收。"""
    src = str(source or "").strip()
    if not src.startswith("http"):
        return []
    out = []
    for text in _summary_lines(summary):
        if len(text) < 8 or len(text) > 180:
            continue
        if text.startswith(("我看了", "这个视频", "一句话", "总结")):
            continue
        out.append({
            "fact": text,
            "source": src,
            "title": str(title or "")[:120],
            "confidence": 0.7,
        })
        if len(out) >= max(1, min(8, int(limit))):
            break
    return out
