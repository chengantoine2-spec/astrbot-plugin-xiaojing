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


def add_facts(topic: str, facts: list[dict]) -> list[dict]:
    data = _load()
    existing = {_norm(x.get("fact")) for x in data["facts"]}
    added = []
    now = int(time.time())
    for item in facts[:6]:
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
