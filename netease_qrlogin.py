# -*- coding: utf-8 -*-
"""网易云扫码登录：拿 unikey → 出二维码 → 轮询 → 成功后 DPAPI 保存 Cookie。

用法：
    python netease_qrlogin.py            # 生成二维码并等待扫码（最长 170 秒）
二维码写到 data/qr_login.png，状态写到 data/qr_status.json。
"""

from __future__ import annotations

import http.cookiejar
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import qrcode

DATA = Path(__file__).resolve().parent / "data"
QR_PNG = DATA / "qr_login.png"
STATUS = DATA / "qr_status.json"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "Chrome/126 Safari/537.36"
)
KEEP = ("MUSIC_U", "__csrf", "MUSIC_A", "NMTID", "_ntes_nuid")


def _status(state: str, **extra) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        json.dumps({"state": state, "ts": int(time.time()), **extra}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[qr] {state} {extra}", flush=True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    headers = {"User-Agent": UA, "Referer": "https://music.163.com/"}

    req = urllib.request.Request(
        "https://music.163.com/api/login/qrcode/unikey?type=1", headers=headers
    )
    j = json.loads(op.open(req, timeout=20).read().decode("utf-8", "ignore"))
    unikey = j.get("unikey") or ""
    if not unikey:
        _status("error", reason=f"unikey 获取失败: {j}")
        return 1

    url = f"https://music.163.com/login?codekey={unikey}"
    img = qrcode.make(url)
    img = img.resize((520, 520))
    DATA.mkdir(parents=True, exist_ok=True)
    img.save(QR_PNG)
    _status("waiting", qr=str(QR_PNG), url=url, key=unikey)

    deadline = time.time() + 300
    scanned = False
    while time.time() < deadline:
        time.sleep(2)
        # 关键：轮询必须不带 Cookie，否则服务端一直回 802
        q = urllib.parse.urlencode({"key": unikey, "type": 1, "noCookie": "true"})
        r = urllib.request.Request(
            f"https://music.163.com/api/login/qrcode/client/login?{q}",
            headers={"User-Agent": UA, "Referer": "https://music.163.com/"},
        )
        try:
            with urllib.request.urlopen(r, timeout=15) as resp:
                raw = resp.read().decode("utf-8", "ignore")
                setc = resp.headers.get_all("Set-Cookie") or []
            data = json.loads(raw)
        except Exception as e:
            _status("error", reason=f"轮询异常: {e}", key=unikey)
            return 1
        code = int(data.get("code") or 0)
        if code == 800:
            _status("expired", key=unikey)
            return 2
        if code == 802 and not scanned:
            scanned = True
            _status("scanned", key=unikey)
            continue
        if code == 803:
            pairs = []
            for line in setc:
                first = line.split(";")[0]
                if first.split("=", 1)[0] in KEEP:
                    pairs.append(first)
            cookie = "; ".join(pairs)
            if "MUSIC_U=" not in cookie:
                jar_cookie = "; ".join(f"{c.name}={c.value}" for c in cj if c.name in KEEP)
                cookie = cookie or jar_cookie
            if "MUSIC_U=" not in cookie:
                _status("error", reason="803 但没拿到 MUSIC_U", key=unikey)
                return 3
            try:
                from netease_cookie import bind_status, normalize_cookie, save_cookie

                cookie = normalize_cookie(cookie)
                info = bind_status(cookie)
                save_cookie(cookie)
            except Exception as e:
                _status("error", reason=f"保存失败: {e}", key=unikey)
                return 4
            _status("ok", account=info, key=unikey)
            return 0
    _status("timeout", key=unikey)
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
