# -*- coding: utf-8 -*-
"""NapCat 守夜人：由 Windows 计划任务定时探测 OneBot HTTP 端口。

- 正常：静默，只更新心跳文件；
- 掉线：写日志 + 桌面气泡通知；
- 若 QQ 进程已不存在，且距上次重启超过 90 分钟，尝试用快速密码拉起 NapCat。

由 Windows 计划任务定时调用，无需常驻。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

def _first_dir(*candidates) -> Path:
    for c in candidates:
        if not c:
            continue
        p = Path(str(c)).expanduser()
        if p.is_dir():
            return p
    return Path(str(candidates[-1])).expanduser()


NAPCAT = _first_dir(
    os.environ.get("NAPCAT_DIR"),
    str(Path.home() / "NapCat" / "NapCat.Shell"),
)
_app_env = os.environ.get("NAPCAT_APP")
if _app_env:
    NAPCAT_APP = Path(_app_env).expanduser()
else:
    _apps = sorted(
        (NAPCAT / "versions").glob("*/resources/app/napcat"),
        key=lambda p: p.stat().st_mtime,
    )
    NAPCAT_APP = _apps[-1] if _apps else NAPCAT / "resources" / "app" / "napcat"
ONEBOT_CFG = NAPCAT_APP / "config" / f"onebot11_{os.environ.get('NAPCAT_ACCOUNT', '')}.json"
QR_CACHE = NAPCAT_APP / "cache" / "qrcode.png"
BOOT_EXE = NAPCAT / "NapCatWinBootMain.exe"
ASTRBOT_ROOT = _first_dir(
    os.environ.get("ASTRBOT_ROOT"),
    str(Path.home() / ".astrbot"),
)
PLUGIN_DATA = ASTRBOT_ROOT / "data" / "plugins" / "astrbot_plugin_xiaojing" / "data"
LOG = PLUGIN_DATA / "watchdog.log"
STATE = PLUGIN_DATA / "watchdog_state.json"
ACCOUNT = os.environ.get("NAPCAT_ACCOUNT", "")
QUICK_PWD = os.environ.get("NAPCAT_QUICK_PASSWORD", "")
RESTART_GAP = 90 * 60


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if LOG.exists() and LOG.stat().st_size > 1024 * 1024:
        LOG.write_text("", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(st: dict) -> None:
    try:
        STATE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def onebot_cfg() -> tuple[int, str]:
    try:
        cfg = json.loads(ONEBOT_CFG.read_text(encoding="utf-8"))
        srv = ((cfg.get("network") or {}).get("httpServers") or [{}])[0]
        return int(srv.get("port") or 3000), str(srv.get("token") or "")
    except Exception:
        return 3000, ""


def probe(port: int, token: str) -> tuple[bool, str]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/get_login_info",
        headers={"Authorization": "Bearer " + token} if token else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            j = json.loads(r.read().decode("utf-8", "ignore"))
        if int(j.get("retcode", -1)) == 0:
            return True, str((j.get("data") or {}).get("nickname") or "")
        return False, f"retcode={j.get('retcode')}"
    except Exception as e:
        return False, str(e)[:60]


def ws_alive() -> bool:
    try:
        out = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=15,
            creationflags=0x08000000,
        ).stdout
        for line in out.splitlines():
            if ":6199" in line and "ESTABLISHED" in line.upper():
                return True
    except Exception:
        pass
    return False


def qq_alive() -> bool:
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq QQ.exe", "/NH"],
            capture_output=True, text=True, timeout=15,
            creationflags=0x08000000,
        ).stdout.lower()
        return "qq.exe" in out
    except Exception:
        return False


def notify(title: str, msg: str) -> None:
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "Add-Type -AssemblyName System.Drawing;"
        "$n=New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon=[System.Drawing.SystemIcons]::Information;"
        "$n.Visible=$true;"
        f"$n.ShowBalloonTip(8000,'{title}','{msg}',"
        "[System.Windows.Forms.ToolTipIcon]::Info);"
        "Start-Sleep -Seconds 8;$n.Dispose()"
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            creationflags=0x08000000,
        )
    except Exception as e:
        log(f"通知失败 {e}")


def restart_napcat() -> bool:
    env = os.environ.copy()
    env["ACCOUNT"] = ACCOUNT
    env["NAPCAT_QUICK_PASSWORD"] = QUICK_PWD
    try:
        subprocess.Popen(
            [str(BOOT_EXE), ACCOUNT],
            cwd=str(NAPCAT),
            env=env,
            creationflags=0x08000000,
        )
        return True
    except Exception as e:
        log(f"重启失败 {e}")
        return False


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    st = load_state()
    port, token = onebot_cfg()
    ok, detail = probe(port, token)

    if ok:
        st["down"] = False
        st["last_ok"] = int(time.time())
        if not ws_alive():
            log(f"HTTP 在线但 WS 未连接：{detail}")
            if not st.get("ws_down"):
                notify("小鲸连接异常", "OneBot HTTP 在线，但 WebSocket 未建立，消息可能收发不了")
            st["ws_down"] = True
            save_state(st)
            return 0
        if st.get("ws_down"):
            log("WS 已恢复")
            notify("小鲸连接恢复", "WebSocket 已重新建立")
        st["ws_down"] = False
        save_state(st)
        return 0

    qr_new = False
    try:
        qr_new = QR_CACHE.exists() and (time.time() - QR_CACHE.stat().st_mtime) < 900
    except Exception:
        pass

    reason = "等待扫码登录" if qr_new else ("QQ 进程在但 OneBot 未响应" if qq_alive() else "QQ/NapCat 已退出")
    log(f"离线：{detail}｜{reason}")

    if not st.get("down"):
        notify("小鲸掉线", f"{reason}。详情见 watchdog.log")
    st["down"] = True
    st["last_fail"] = int(time.time())

    if not qr_new and not qq_alive():
        last = int(st.get("last_restart") or 0)
        if time.time() - last > RESTART_GAP:
            if restart_napcat():
                st["last_restart"] = int(time.time())
                log("已尝试快速登录拉起 NapCat")
                notify("正在尝试唤醒", "已拉起 NapCat，若弹二维码需要扫码")
    save_state(st)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
