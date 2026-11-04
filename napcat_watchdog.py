# -*- coding: utf-8 -*-
"""NapCat 看门狗：定时探测 OneBot HTTP 端口。

- 00:00-06:00 夜间静默：不探测、不重启、不弹通知
- 06:00-07:00 之间做一次当日重启，重启后由正常探测接管
- 在线时只写日志，不打扰
- 掉线时写日志 + 桌面通知
- 若 QQ 进程已不在，拉起 NapCat（最多每 90 分钟一次，避免反复拉起）
- 账号自动从 onebot11_*.json 中识别，避免重启后变成扫码登录

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

try:
    import psutil
except Exception:  # pragma: no cover - AstrBot 自带 psutil；缺失时退化为只停引导进程
    psutil = None


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
    r"D:\NapCat\NapCat.52230.Shell",
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

BOOT_EXE = NAPCAT / "NapCatWinBootMain.exe"
QR_CACHE = NAPCAT_APP / "cache" / "qrcode.png"
ASTRBOT_ROOT = _first_dir(
    os.environ.get("ASTRBOT_ROOT"),
    r"D:\AstrBotData",
    str(Path.home() / ".astrbot"),
)
PLUGIN_DATA = ASTRBOT_ROOT / "data" / "plugins" / "astrbot_plugin_xiaojing" / "data"
LOG = PLUGIN_DATA / "watchdog.log"
STATE = PLUGIN_DATA / "watchdog_state.json"

QUIET_START = os.environ.get("NAPCAT_QUIET_START", "00:00")
QUIET_END = os.environ.get("NAPCAT_QUIET_END", "06:00")
DAILY_RESTART = os.environ.get("NAPCAT_DAILY_RESTART", "06:00")
DAILY_RESTART_ENABLED = os.environ.get("NAPCAT_DAILY_RESTART_ENABLED", "1").lower() not in (
    "0", "false", "no", "off",
)
RESTART_GAP = 90 * 60
DAILY_WINDOW_MINUTES = 60


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


def _clock_minutes(value, fallback: int) -> int:
    try:
        h, m = str(value).strip().split(":")
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h * 60 + m
    except Exception:
        pass
    return fallback


def _hm(ts: float | None = None) -> str:
    return time.strftime("%H:%M", time.localtime(time.time() if ts is None else ts))


def _day(ts: float | None = None) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(time.time() if ts is None else ts))


def in_quiet(ts: float | None = None) -> bool:
    cur = _clock_minutes(_hm(ts), -1)
    start = _clock_minutes(QUIET_START, 0)
    end = _clock_minutes(QUIET_END, 6 * 60)
    if cur < 0 or start == end:
        return False
    if start < end:
        return start <= cur < end
    return cur >= start or cur < end


def recent_restart(st: dict, now: float, grace: float = 600) -> bool:
    return now - int(st.get("last_restart") or 0) < grace


def daily_restart_due(st: dict, ts: float | None = None) -> bool:
    if not DAILY_RESTART_ENABLED:
        return False
    ts = time.time() if ts is None else ts
    cur = _clock_minutes(_hm(ts), -1)
    target = _clock_minutes(DAILY_RESTART, 6 * 60)
    if cur < 0:
        return False
    if not (target <= cur < min(target + DAILY_WINDOW_MINUTES, 24 * 60)):
        return False
    return str(st.get("daily_restart_day") or "") != _day(ts)


def detect_account() -> str:
    """从 onebot11_*.json 里找出当前启用的账号，避免重启后要求扫码。"""
    env = os.environ.get("NAPCAT_ACCOUNT", "").strip()
    if env:
        return env
    try:
        candidates = list((NAPCAT_APP / "config").glob("onebot11_*.json"))
    except Exception:
        candidates = []
    parsed = []
    for p in candidates:
        try:
            parsed.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except Exception:
            continue
    # 优先：启用了指向本机 6199 的 WebSocket 客户端
    for p, cfg in parsed:
        for client in ((cfg.get("network") or {}).get("websocketClients") or []):
            if client.get("enable") and "127.0.0.1:6199" in str(client.get("url") or ""):
                return p.stem.replace("onebot11_", "", 1)
    # 其次：启用了 HTTP 服务
    for p, cfg in parsed:
        servers = ((cfg.get("network") or {}).get("httpServers") or [])
        if servers and servers[0].get("enable"):
            return p.stem.replace("onebot11_", "", 1)
    return ""


ACCOUNT = detect_account()
ONEBOT_CFG = NAPCAT_APP / "config" / f"onebot11_{ACCOUNT}.json"
QUICK_PWD = os.environ.get("NAPCAT_QUICK_PASSWORD", "")


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


def _napcat_processes() -> list:
    """只找 D:\\NapCat 下的 QQ 和引导进程，避免误杀个人 QQ。"""
    if psutil is None:
        return []
    targets = []
    napcat_root = str(NAPCAT).lower()
    for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
        try:
            name = str(proc.info.get("name") or "").lower()
            exe = str(proc.info.get("exe") or "").lower()
            cmd = " ".join(proc.info.get("cmdline") or []).lower()
            if name == "napcatwinbootmain.exe":
                targets.append(proc)
                continue
            if name == "qq.exe" and (
                napcat_root in exe
                or ("--enable-logging" in cmd and napcat_root in cmd)
            ):
                targets.append(proc)
        except Exception:
            continue
    return targets


def stop_napcat(dry_run: bool = False) -> list[int]:
    procs = _napcat_processes()
    if not procs:
        return []
    if dry_run:
        return [int(p.pid) for p in procs]
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    _, alive = psutil.wait_procs(procs, timeout=6)
    for p in alive:
        try:
            p.kill()
        except Exception:
            pass
    log("已停止 NapCat 进程：" + ", ".join(f"{p.info.get('name')}#{p.pid}" for p in procs))
    time.sleep(2)
    return [int(p.pid) for p in procs]


def restart_napcat() -> bool:
    if not ACCOUNT:
        log("未识别 NapCat 账号，跳过重启（避免扫码登录）")
        return False
    if not BOOT_EXE.exists():
        log(f"找不到启动器：{BOOT_EXE}")
        return False
    stop_napcat()
    env = os.environ.copy()
    env["ACCOUNT"] = ACCOUNT
    if QUICK_PWD:
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
        log(f"启动失败 {e}")
        return False


def main() -> int:
    # pythonw.exe 下 sys.stdout 是 None，直接 reconfigure 会异常退出。
    try:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    st = load_state()
    now = time.time()

    # 夜间静默：不探测、不重启、不通知。每天只记一条。
    if in_quiet(now):
        day = _day(now)
        if st.get("quiet_day") != day:
            st["quiet_day"] = day
            log(f"夜间静默 {QUIET_START}-{QUIET_END}：不探测、不重启、不通知")
            save_state(st)
        return 0

    # 早上做一次当日重启，随后交给正常探测。
    if daily_restart_due(st, now):
        day = _day(now)
        if not ACCOUNT:
            log("未识别 NapCat 账号，跳过定时重启（避免扫码登录）")
            st["daily_restart_day"] = day
            save_state(st)
            return 1
        log(f"{DAILY_RESTART} 定时重启 NapCat（账号 {ACCOUNT}）")
        if not QUICK_PWD:
            log("提示：未配置 NAPCAT_QUICK_PASSWORD；若未自动登录，需要在 NapCat 扫码")
        ok = restart_napcat()
        st["last_restart"] = int(now)
        st["daily_restart_day"] = day
        save_state(st)
        return 0 if ok else 1

    port, token = onebot_cfg()
    ok, detail = probe(port, token)

    if ok:
        st["down"] = False
        st["last_ok"] = int(now)
        if not ws_alive():
            log(f"HTTP 在线但 WS 未连接：{detail}")
            if not st.get("ws_down") and not recent_restart(st, now):
                notify("小鲸连接异常", "OneBot HTTP 在线，但 WebSocket 未连接，消息可能收不到。")
            st["ws_down"] = True
            save_state(st)
            return 0
        if st.get("ws_down"):
            log("WS 已恢复")
            notify("小鲸连接恢复", "WebSocket 已重新连接。")
        st["ws_down"] = False
        save_state(st)
        return 0

    qr_new = False
    try:
        qr_new = QR_CACHE.exists() and (time.time() - QR_CACHE.stat().st_mtime) < 900
    except Exception:
        pass

    reason = "等待扫码登录" if qr_new else ("QQ 进程在但 OneBot 未响应" if qq_alive() else "QQ/NapCat 进程已退出")
    log(f"掉线：{detail}；{reason}")

    if not st.get("down") and not recent_restart(st, now):
        notify("小鲸掉线", f"{reason}，详情见 watchdog.log")
    st["down"] = True
    st["last_fail"] = int(now)

    if not qr_new and not qq_alive():
        last = int(st.get("last_restart") or 0)
        if now - last > RESTART_GAP:
            if restart_napcat():
                st["last_restart"] = int(now)
                log("已尝试快速登录并拉起 NapCat")
                if not recent_restart(st, now):
                    notify("正在尝试恢复", "正在拉起 NapCat；若未配置快速登录，需要扫码。")
    save_state(st)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
