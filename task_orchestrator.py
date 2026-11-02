# -*- coding: utf-8 -*-
"""轻量任务编排：并行 worker、超时、失败隔离、结构化结果。"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class TaskResult:
    kind: str
    ok: bool
    data: Any = None
    error: str = ""
    elapsed: float = 0.0
    meta: dict = field(default_factory=dict)


class TaskOrchestrator:
    def __init__(self, limit: int = 4):
        self.limit = max(1, int(limit))
        self._sem = asyncio.Semaphore(self.limit)

    async def run(self, kind: str, factory: Callable[[], Awaitable[Any]],
                  timeout: float = 30.0, meta: dict | None = None) -> TaskResult:
        started = time.time()
        try:
            async with self._sem:
                data = await asyncio.wait_for(factory(), timeout=max(1, float(timeout)))
            return TaskResult(kind=kind, ok=True, data=data,
                              elapsed=time.time() - started, meta=meta or {})
        except asyncio.TimeoutError:
            return TaskResult(kind=kind, ok=False, error="timeout",
                              elapsed=time.time() - started, meta=meta or {})
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return TaskResult(kind=kind, ok=False, error=f"{type(e).__name__}: {e}",
                              elapsed=time.time() - started, meta=meta or {})

    async def gather(self, tasks: list[tuple[str, Callable[[], Awaitable[Any]]]],
                     timeout: float = 40.0) -> list[TaskResult]:
        if not tasks:
            return []
        return list(await asyncio.gather(
            *(self.run(kind, factory, timeout=timeout) for kind, factory in tasks)
        ))
