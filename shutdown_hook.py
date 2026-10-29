# -*- coding: utf-8 -*-
"""关机 / 睡眠 / 注销前发一条固定消息。

原理：创建一个隐藏的顶层窗口，接收 Windows 广播：
- WM_QUERYENDSESSION（关机或注销）
- WM_POWERBROADCAST / PBT_APMSUSPEND（睡眠）

发送走 NapCat 的 HTTP 接口，同步、短超时，确保在系统给的几秒内完成。
"""

from __future__ import annotations

import threading
import time
from typing import Callable

WM_QUERYENDSESSION = 0x0011
WM_POWERBROADCAST = 0x0218
PBT_APMSUSPEND = 0x0004
ENDSESSION_LOGOFF = 0x80000000
CLASS_NAME = "XiaojingShutdownHookWnd"


class _Hook(threading.Thread):
    def __init__(self, send: Callable[[str], None]):
        super().__init__(daemon=True, name="xiaojing-shutdown-hook")
        self._send = send
        self._last = 0.0

    def _fire(self, kind: str) -> None:
        now = time.time()
        if now - self._last < 5:
            return
        self._last = now
        try:
            self._send(kind)
        except Exception:
            pass

    def run(self) -> None:
        try:
            import win32gui
        except Exception:
            return

        def proc(hwnd, msg, wparam, lparam):
            if msg == WM_QUERYENDSESSION:
                kind = "logoff" if (int(lparam) & ENDSESSION_LOGOFF) else "shutdown"
                self._fire(kind)
                return 1
            if msg == WM_POWERBROADCAST and int(wparam) == PBT_APMSUSPEND:
                self._fire("sleep")
                return 1
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        try:
            wc = win32gui.WNDCLASS()
            wc.hInstance = win32gui.GetModuleHandle(None)
            wc.lpszClassName = CLASS_NAME
            wc.lpfnWndProc = proc
            atom = win32gui.RegisterClass(wc)
            hwnd = win32gui.CreateWindow(
                atom, "xiaojing", 0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
            )
            # 不显示窗口，只收广播消息
            win32gui.PumpMessages()
        except Exception:
            return


def start_shutdown_hook(send: Callable[[str], None]) -> bool:
    """启动钩子；失败返回 False，不影响主程序。"""
    try:
        _Hook(send).start()
        return True
    except Exception:
        return False
