# -*- coding: utf-8 -*-
"""轻量任务编排：并行 worker、超时、失败隔离、计划与汇总。"""

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


@dataclass
class TaskSpec:
    kind: str
    factory: Callable[[], Awaitable[Any]]
    timeout: float = 30.0
    required: bool = False
    meta: dict = field(default_factory=dict)


@dataclass
class PlanResult:
    name: str
    ok: bool
    results: list[TaskResult]
    data: Any = None
    elapsed: float = 0.0


class Aggregator:
    """常用汇总：取第一个成功、收集全部成功、合并字典。"""

    @staticmethod
    def first_ok(results: list[TaskResult], kinds: set[str] | None = None) -> Any:
        for r in results:
            if r.ok and (not kinds or r.kind in kinds):
                return r.data
        return None

    @staticmethod
    def collect(results: list[TaskResult], kinds: set[str] | None = None) -> list[Any]:
        return [r.data for r in results
                if r.ok and r.data is not None and (not kinds or r.kind in kinds)]

    @staticmethod
    def merge_dicts(results: list[TaskResult], kinds: set[str] | None = None) -> dict:
        out: dict = {}
        for r in results:
            if r.ok and isinstance(r.data, dict) and (not kinds or r.kind in kinds):
                out.update(r.data)
        return out


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

    async def run_plan(self, name: str, specs: list[TaskSpec],
                       aggregate: Callable[[list[TaskResult]], Any] | None = None,
                       timeout: float | None = None) -> PlanResult:
        """执行一份计划；必选任务失败则整体失败，可选任务失败只记录。"""
        started = time.time()
        if not specs:
            return PlanResult(name=name, ok=False, results=[], data=None, elapsed=0.0)
        results = list(await asyncio.gather(*(
            self.run(
                spec.kind,
                spec.factory,
                timeout=min(float(spec.timeout), float(timeout)) if timeout else spec.timeout,
                meta=spec.meta,
            )
            for spec in specs
        )))
        required_ok = all(r.ok for spec, r in zip(specs, results) if spec.required)
        ok = required_ok and any(r.ok for r in results)
        data = aggregate(results) if aggregate else None
        return PlanResult(name=name, ok=ok, results=results, data=data,
                          elapsed=time.time() - started)
