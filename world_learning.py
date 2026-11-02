# -*- coding: utf-8 -*-
"""小鲸鱼的世界记忆：公开网页研究得到的事实，带来源、时间、置信度。"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WORLD_DIR = DATA_DIR / "world"
FACTS_PATH = WORLD_DIR / "facts.json"
NOTES_PATH = WORLD_DIR / "notes.json"
STATE_PATH = WORLD_DIR / "state.json"


def _load() -> dict:
    try:
        data = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("facts", [])
            return data
    except Exception:
        pass
    return {"facts": []}


def _save(data: dict) -> None:
    try:
        WORLD_DIR.mkdir(parents=True, exist_ok=True)
        data["facts"] = (data.get("facts") or [])[-500:]
        data["updated"] = int(time.time())
        FACTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    except Exception:
        pass


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "")).lower()[:200]


def add_facts(topic: str, facts: list[dict], limit: int = 8) -> list[dict]:
    data = _load()
    existing = {_norm(x.get("fact")) for x in data["facts"]}
    added = []
    now = int(time.time())
    for item in facts[: max(1, min(12, int(limit)))]:
        if not isinstance(item, dict):
            continue
        fact = re.sub(r"\s+", " ", str(item.get("fact") or "")).strip()
        source = str(item.get("source") or "").strip()
        if not fact or not source or len(fact) < 8:
            continue
        key = _norm(fact)
        if key in existing:
            continue
        try:
            conf = max(0.0, min(1.0, float(item.get("confidence") or 0.5)))
        except Exception:
            conf = 0.5
        row = {
            "id": "wf" + hashlib.sha1(f"{topic}:{fact}:{now}".encode()).hexdigest()[:12],
            "topic": str(topic or "")[:80],
            "fact": fact[:400],
            "source": source[:500],
            "title": str(item.get("title") or "")[:120],
            "confidence": conf,
            "seen_at": now,
        }
        data["facts"].append(row)
        existing.add(key)
        added.append(row)
    if added:
        _save(data)
    return added


def list_facts(limit: int = 10, keyword: str = "") -> list[dict]:
    facts = _load().get("facts", [])
    if keyword:
        q = str(keyword).lower()
        facts = [x for x in facts
                 if q in str(x.get("fact") or "").lower()
                 or q in str(x.get("topic") or "").lower()
                 or q in str(x.get("source") or "").lower()]
    return sorted(facts, key=lambda x: x.get("seen_at", 0), reverse=True)[:limit]


def remove_facts(keyword: str) -> int:
    q = str(keyword or "").strip().lower()
    if not q:
        return 0
    data = _load()
    old = data.get("facts", [])
    keep = [x for x in old if q not in str(x.get("fact") or "").lower()
            and q not in str(x.get("topic") or "").lower()]
    data["facts"] = keep
    _save(data)
    return len(old) - len(keep)


def format_facts(limit: int = 10, keyword: str = "") -> str:
    items = list_facts(limit, keyword)
    if not items:
        return "世界记忆里还没有相关条目。"
    lines = [f"世界记忆 {len(_load().get('facts', []))} 条，最近 {len(items)} 条："]
    for x in items:
        lines.append(f"- [{x.get('topic') or '未分类'}] {x.get('fact')}")
        lines.append(f"  来源：{x.get('source')}")
    return "\n".join(lines)


# ---------------- 完整学习笔记 ----------------

def _load_notes() -> dict:
    try:
        data = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("notes", [])
            return data
    except Exception:
        pass
    return {"notes": []}


def _save_notes(data: dict) -> None:
    try:
        WORLD_DIR.mkdir(parents=True, exist_ok=True)
        data["notes"] = (data.get("notes") or [])[-120:]
        data["updated"] = int(time.time())
        NOTES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    except Exception:
        pass


def add_note(topic: str, summary: str, facts: list[dict],
             docs: list[dict], usage: dict | None = None) -> dict:
    """按主题保存完整笔记：摘要、要点、来源摘录和本次用量。"""
    topic = re.sub(r"\s+", " ", str(topic or "")).strip()[:80]
    summary = re.sub(r"\s+", " ", str(summary or "")).strip()[:1200]
    if not topic or not summary:
        return {}
    now = int(time.time())
    points = []
    seen = set()
    for item in (facts or [])[:12]:
        if not isinstance(item, dict):
            continue
        fact = re.sub(r"\s+", " ", str(item.get("fact") or "")).strip()
        key = _norm(fact)
        if not fact or key in seen:
            continue
        seen.add(key)
        points.append({
            "fact": fact[:300],
            "source": str(item.get("source") or "")[:500],
            "title": str(item.get("title") or "")[:120],
        })
    sources = []
    for d in (docs or [])[:6]:
        if not isinstance(d, dict):
            continue
        url = str(d.get("url") or "").strip()
        if not url:
            continue
        text = re.sub(r"\s+", " ", str(d.get("text") or "")).strip()
        sources.append({
            "title": str(d.get("title") or "")[:160],
            "url": url[:500],
            "excerpt": text[:800],
        })
    note = {
        "id": "wnt" + hashlib.sha1(f"{topic}:{now}".encode()).hexdigest()[:12],
        "topic": topic,
        "summary": summary,
        "points": points,
        "sources": sources,
        "usage": {
            "prompt": int((usage or {}).get("prompt") or 0),
            "completion": int((usage or {}).get("completion") or 0),
            "cost": float((usage or {}).get("cost") or 0.0),
        },
        "created": now,
        "updated": now,
    }
    data = _load_notes()
    notes = data.get("notes") or []
    old = next((x for x in notes if _norm(x.get("topic")) == _norm(topic)), None)
    if old:
        note["created"] = int(old.get("created") or now)
        notes[notes.index(old)] = note
    else:
        notes.append(note)
    data["notes"] = notes
    _save_notes(data)
    return note


def list_notes(limit: int = 10, keyword: str = "") -> list[dict]:
    notes = _load_notes().get("notes", [])
    if keyword:
        q = str(keyword).lower()
        notes = [x for x in notes
                 if q in str(x.get("topic") or "").lower()
                 or q in str(x.get("summary") or "").lower()]
    return sorted(notes, key=lambda x: x.get("updated", 0), reverse=True)[:max(1, int(limit))]


def get_note(topic: str) -> dict:
    q = str(topic or "").strip()
    if not q:
        return {}
    notes = _load_notes().get("notes", [])
    exact = next((x for x in notes if str(x.get("topic") or "") == q), None)
    if exact:
        return exact
    return next((x for x in notes if q.lower() in str(x.get("topic") or "").lower()), {})


def remove_notes(keyword: str) -> int:
    q = str(keyword or "").strip().lower()
    if not q:
        return 0
    data = _load_notes()
    old = data.get("notes", [])
    keep = [x for x in old
            if q not in str(x.get("topic") or "").lower()
            and q not in str(x.get("summary") or "").lower()]
    data["notes"] = keep
    _save_notes(data)
    return len(old) - len(keep)


def format_notes(limit: int = 10, keyword: str = "") -> str:
    all_notes = _load_notes().get("notes", [])
    items = list_notes(limit, keyword)
    if not items:
        return "还没有完整学习笔记。让我学一个主题，比如「学习 深海生物」。"
    lines = [f"学习笔记 {len(all_notes)} 个主题，最近 {len(items)} 个："]
    for n in items:
        points = n.get("points") or []
        stamp = time.strftime("%m-%d %H:%M", time.localtime(int(n.get("updated") or 0)))
        lines.append(f"- {n.get('topic')}（{len(points)} 条要点，{stamp}）")
        lines.append(f"  {str(n.get('summary') or '')[:90]}")
    lines.append("用「世界笔记 主题」看完整内容。")
    return "\n".join(lines)[:1800]


def format_note(topic: str) -> str:
    note = get_note(topic)
    if not note:
        items = list_facts(20, topic)
        if items:
            lines = [f"《{topic}》还没有完整笔记，先看世界记忆里的短事实："]
            for x in items:
                lines.append(f"- {x.get('fact')}")
                lines.append(f"  来源：{x.get('source')}")
            lines.append("下次学习这个主题会补全摘要和来源摘录。")
            return "\n".join(lines)[:2600]
        return f"没找到「{topic}」的学习笔记。用「世界笔记」看已有主题。"
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(note.get("updated") or 0)))
    sources = note.get("sources") or []
    source_index = {str(s.get("url") or ""): i + 1 for i, s in enumerate(sources)}
    lines = [f"《{note.get('topic')}》学习笔记（{stamp}）", "", f"摘要：{note.get('summary')}", "", "要点："]
    for p in (note.get("points") or [])[:12]:
        ref = source_index.get(str(p.get("source") or ""))
        lines.append(f"- {p.get('fact')}" + (f" [资料{ref}]" if ref else ""))
    if sources:
        lines.append("")
        lines.append("读过的资料：")
        for i, s in enumerate(sources[:6], 1):
            lines.append(f"[资料{i}] {s.get('title') or '资料'}")
            lines.append(f"  {s.get('url')}")
            if s.get("excerpt"):
                lines.append(f"  摘录：{str(s.get('excerpt'))[:260]}…")
    usage = note.get("usage") or {}
    used = int(usage.get("prompt") or 0) + int(usage.get("completion") or 0)
    if used:
        lines.append("")
        lines.append(f"这次学习用了 {used} token。")
    return "\n".join(lines)[:5200]


def load_state() -> dict:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(data: dict) -> None:
    try:
        WORLD_DIR.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                              encoding="utf-8")
    except Exception:
        pass
