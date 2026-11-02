# -*- coding: utf-8 -*-
"""小鲸鱼的本地角色素材库。

- 三视图、姿势、表情、场景都登记在 data/assets/library.json
- 按活动/心情/标签打分选择，找不到就返回 None，由调用方回退
"""

from __future__ import annotations

import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LIB_PATH = DATA_DIR / "assets" / "library.json"


def load() -> dict:
    try:
        data = json.loads(LIB_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def assets(kind: str = "") -> list[dict]:
    items = load().get("assets") or []
    if kind:
        items = [a for a in items if str(a.get("type") or "") == kind]
    return [a for a in items if isinstance(a, dict)]


def pick(activity: str = "", kind: str = "", mood: str = "", rng=None) -> dict | None:
    """按标签给素材打分；同分随机，避免每次都同一张。"""
    items = assets(kind)
    if not kind:
        # 默认不拿三视图当自拍素材
        items = [a for a in items if str(a.get("type") or "") != "sheet"]
    if not items:
        return None
    act = str(activity or "")
    mood = str(mood or "")
    best_score = -1
    pool: list[dict] = []
    for item in items:
        tags = [str(t) for t in (item.get("tags") or [])]
        preferred = [str(x) for x in (item.get("preferred") or [])]
        score = 0
        if act and act in preferred:
            score += 20
        if act and act in tags:
            score += 8
        if mood and mood in tags:
            score += 3
        for tag in tags:
            if tag and tag in act:
                score += 2
        if score > best_score:
            best_score = score
            pool = [item]
        elif score == best_score:
            pool.append(item)
    return (rng or random).choice(pool)


def resolve(item: dict | None) -> Path | None:
    """把素材相对路径解析为本地绝对路径，拒绝越出 data 目录。"""
    if not isinstance(item, dict):
        return None
    rel = str(item.get("path") or "").strip()
    if not rel:
        return None
    fp = (DATA_DIR / rel).resolve()
    try:
        fp.relative_to(DATA_DIR.resolve())
    except Exception:
        return None
    return fp if fp.exists() else None
