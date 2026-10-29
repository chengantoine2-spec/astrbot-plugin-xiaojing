# -*- coding: utf-8 -*-
"""网易云 Cookie 本地加密存储（Windows DPAPI）。

- 密文写在 data/netease.enc，只有当前 Windows 用户能解密；
- 不写日志、不回显、不进对话；
- 命令行：
    python netease_cookie.py set      # 粘贴 Cookie（不回显），校验后保存
    python netease_cookie.py status   # 查看绑定账号与会员状态
    python netease_cookie.py clear    # 解除绑定
"""

from __future__ import annotations

import getpass
import json
import os
import sys
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
ENC = DATA / "netease.enc"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
REF = "https://music.163.com/"


def _protect(text: str) -> bytes:
    import win32crypt

    return win32crypt.CryptProtectData(
        text.encode("utf-8"), "xiaojing-netease", None, None, None, 0
    )


def _unprotect(blob: bytes) -> str:
    import win32crypt

    return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode("utf-8")


def save_cookie(cookie: str) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    ENC.write_bytes(_protect(cookie.strip()))
    try:
        os.chmod(ENC, 0o600)
    except Exception:
        pass


def load_cookie() -> str:
    try:
        return _unprotect(ENC.read_bytes()).strip()
    except Exception:
        return ""


def clear_cookie() -> None:
    try:
        ENC.unlink()
    except Exception:
        pass


def _get(url: str, cookie: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Referer": REF, "Cookie": cookie},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def bind_status(cookie: str) -> str:
    """返回一行账号状态；失败抛异常。"""
    j = _get("https://music.163.com/api/nuser/account/get", cookie)
    code = j.get("code")
    if code != 200:
        raise RuntimeError(f"账号接口返回 code={code}")
    profile = j.get("profile") or {}
    if not profile:
        raise RuntimeError("Cookie 无效或已过期（拿不到账号信息）")
    nick = profile.get("nickname") or "?"
    uid = profile.get("userId") or "?"
    vtype = int(profile.get("vipType") or 0)
    label = {0: "普通用户", 10: "音乐包", 11: "黑胶 VIP", 110: "黑胶 VIP + 音乐包"}.get(
        vtype, f"vipType={vtype}"
    )
    return f"{nick}（UID {uid}）· {label}"


def normalize_cookie(raw: str) -> str:
    raw = raw.replace("；", ";").replace("，", ";").replace("\u3000", " ")
    parts = [p.strip() for p in raw.replace("\n", ";").split(";") if p.strip()]
    keep = [
        p
        for p in parts
        if p.split("=", 1)[0].strip()
        in ("MUSIC_U", "MUSIC_A", "__csrf", "NMTID", "MUSIC_R_U", "_ntes_nuid")
    ]
    if not any(p.startswith("MUSIC_U=") for p in keep):
        raise RuntimeError("Cookie 里没有 MUSIC_U，无法作为登录态")
    return "; ".join(keep)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "").strip().lower()
    if cmd == "set":
        raw = getpass.getpass("粘贴网易云 Cookie（输入不回显，回车结束）: ").strip()
        if not raw:
            print("没有输入。")
            return 1
        cookie = normalize_cookie(raw)
        try:
            info = bind_status(cookie)
        except Exception as e:
            print(f"校验失败：{e}")
            return 1
        save_cookie(cookie)
        print(f"已保存（DPAPI 加密）→ {ENC}")
        print(f"绑定账号：{info}")
        return 0
    if cmd == "status":
        cookie = load_cookie()
        if not cookie:
            print("尚未绑定网易云 Cookie。")
            return 1
        try:
            print("绑定账号：" + bind_status(cookie))
            return 0
        except Exception as e:
            print(f"Cookie 已失效：{e}")
            return 1
    if cmd == "clear":
        clear_cookie()
        print("已解除绑定。")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
