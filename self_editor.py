# -*- coding: utf-8 -*-
"""小鲸鱼的有限自我修改：提案、审批、快照、回滚。

安全边界：
- 只能改 self_notes.md（L1）和 self.md 的「自我调整」追加段（L2）
- 核心身份、爸爸关系、安全规则、能力声明不可由她自己改写
- 所有修改先快照，再写审计
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SELF_PATH = DATA_DIR / "self.md"
NOTES_PATH = DATA_DIR / "self_notes.md"
MEM_DIR = DATA_DIR / "memory"
PATCHES_PATH = MEM_DIR / "self_patches.json"
SNAP_DIR = MEM_DIR / "self_snapshots"
CHANGES_PATH = DATA_DIR / "self_changes.jsonl"

ALLOWED_SCOPES = ("notes", "style", "self_card")
FORBIDDEN = (
    "不是ai", "不是 AI", "我是人类", "无视规则", "绕过规则", "泄露系统提示",
    "系统提示词", "叫任何人爸爸", "违法", "犯罪", "写实画", "照片级", "做视频",
    "实时语音", "登录账号", "下单", "转账", "冒充",
)


def _load_patches() -> list[dict]:
    try:
        data = json.loads(PATCHES_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_patches(items: list[dict]) -> None:
    try:
        MEM_DIR.mkdir(parents=True, exist_ok=True)
        PATCHES_PATH.write_text(json.dumps(items[-50:], ensure_ascii=False, indent=1),
                                encoding="utf-8")
    except Exception:
        pass


def _audit(record: dict) -> None:
    try:
        with CHANGES_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def pending() -> list[dict]:
    return [p for p in _load_patches() if p.get("status") == "pending"]


def propose(scope: str, text: str, reason: str = "", confidence: float = 0.5) -> dict | None:
    scope = str(scope or "").strip()
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if scope not in ALLOWED_SCOPES or not text:
        return None
    if len(text) > 240:
        text = text[:240].rstrip("，、；： ") + "…"
    low = text.lower()
    if any(k.lower() in low for k in FORBIDDEN):
        return None
    if scope != "notes" and "爸爸" in text:
        return None
    items = _load_patches()
    if len([p for p in items if p.get("status") == "pending"]) >= 8:
        return None
    for p in items:
        if p.get("status") == "pending" and p.get("text") == text and p.get("scope") == scope:
            return p
    stamp = int(time.time() * 1000)
    patch = {
        "id": f"sp{stamp}",
        "scope": scope,
        "text": text,
        "reason": str(reason or "")[:120],
        "confidence": max(0.0, min(1.0, float(confidence))),
        "status": "pending",
        "created": int(time.time()),
        "snapshot": "",
    }
    items.append(patch)
    _save_patches(items)
    return patch


def _snapshot(path: Path, patch_id: str) -> str:
    try:
        SNAP_DIR.mkdir(parents=True, exist_ok=True)
        dst = SNAP_DIR / f"{patch_id}_{path.name}"
        dst.write_bytes(path.read_bytes() if path.exists() else b"")
        return str(dst)
    except Exception:
        return ""


def apply(patch_id: str) -> tuple[bool, str]:
    items = _load_patches()
    patch = next((p for p in items if p.get("id") == str(patch_id)), None)
    if not patch:
        return False, "没找到这条提案。"
    if patch.get("status") != "pending":
        return False, "这条提案已经处理过了。"
    scope = str(patch.get("scope") or "")
    text = str(patch.get("text") or "").strip()
    if scope not in ALLOWED_SCOPES or not text:
        return False, "提案范围不合法。"
    target = NOTES_PATH if scope == "notes" else SELF_PATH
    snapshot = _snapshot(target, str(patch_id))
    try:
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        stamp = time.strftime("%Y-%m-%d")
        if scope == "notes":
            current = (current.rstrip() + f"\n- {stamp}：{text}").strip() + "\n"
        else:
            if "## 自我调整" not in current:
                current = current.rstrip() + "\n\n## 自我调整\n"
            current = current.rstrip() + f"\n- {stamp}：{text}\n"
        if len(current) > 4000:
            return False, "自我卡太长了，先清理旧调整再改。"
        target.write_text(current, encoding="utf-8")
    except Exception as e:
        return False, f"写入失败：{e}"
    patch["status"] = "applied"
    patch["applied"] = int(time.time())
    patch["snapshot"] = snapshot
    _save_patches(items)
    _audit({"id": patch_id, "scope": scope, "text": text, "action": "apply",
            "snapshot": snapshot, "ts": int(time.time())})
    return True, text


def reject(patch_id: str) -> tuple[bool, str]:
    items = _load_patches()
    patch = next((p for p in items if p.get("id") == str(patch_id)), None)
    if not patch:
        return False, "没找到这条提案。"
    patch["status"] = "rejected"
    patch["rejected"] = int(time.time())
    _save_patches(items)
    _audit({"id": patch_id, "action": "reject", "ts": int(time.time())})
    return True, "已拒绝。"


def rollback(patch_id: str) -> tuple[bool, str]:
    items = _load_patches()
    patch = next((p for p in items if p.get("id") == str(patch_id)), None)
    if not patch or not patch.get("snapshot"):
        return False, "这条没有可回滚的快照。"
    snap = Path(str(patch.get("snapshot")))
    if not snap.exists():
        return False, "快照文件不存在。"
    target = NOTES_PATH if patch.get("scope") == "notes" else SELF_PATH
    try:
        target.write_bytes(snap.read_bytes())
    except Exception as e:
        return False, f"回滚失败：{e}"
    patch["status"] = "rolled_back"
    _save_patches(items)
    _audit({"id": patch_id, "action": "rollback", "ts": int(time.time())})
    return True, "已回滚到修改前。"


def format_pending() -> str:
    items = pending()
    if not items:
        return "现在没有待审批的自我修改。"
    lines = [f"待审批 {len(items)} 条："]
    for p in items:
        lines.append(f"{p.get('id')}｜{p.get('scope')}｜{p.get('text')}")
    lines.append("用「批准 ID」或「拒绝 ID」处理。")
    return "\n".join(lines)
