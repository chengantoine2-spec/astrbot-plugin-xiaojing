# 并发与任务编排（Orchestration）

## 为什么先做这个

AstrBot 是异步事件驱动，多个群可能同时来消息。小鲸鱼原来用全局 `self._umo` 保存当前会话，并发时可能把回复、表情包、图片发到另一个群。

## 已完成

### 1. 请求级会话上下文

- `CURRENT_UMO` 是 `contextvars.ContextVar`
- `self._umo` 改为属性：
  - 当前异步任务内读写自己的会话
  - 后台任务回退到 `self._last_umo`
- 同一会话的发送用 `asyncio.Lock` 串行，避免两个回复交错
- 不同会话仍可并行

### 2. 轻量任务编排器

`task_orchestrator.py`：

```python
results = await orchestrator.gather([
    ("vision_compare", lambda: self._vision_compare(images, text)),
    ("compare_image", lambda: asyncio.to_thread(image_edit.compare_images, a, b)),
], timeout=40)
```

每个任务：

- 独立超时
- 失败隔离，返回 `TaskResult(ok=False, error=...)`
- 受全局信号量限制（默认 4 并发）
- 结果由调用方汇总，不直接回复用户

当前已接在“多图对比 + 对比图生成”上：视觉分析和图片渲染并行，谁失败都不影响另一个。

## 下一步

- Planner：判断哪些消息需要拆任务
- Worker 注册表：vision / ocr / image / web / video / memory
- Aggregator：汇总、去重、冲突解决
- 长任务后台执行与取消
- 任务 trace、耗时、费用统计
