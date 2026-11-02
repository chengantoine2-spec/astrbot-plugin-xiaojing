# 视频学习（Video Learning）· P2

小鲸鱼看视频的原则：**字幕优先 → 无字幕 ASR → 关键帧补画面 → 时间戳笔记 → 世界记忆**。

## 已落地

### 1. 视频解析

`video_reader.py`：

- B 站 BV/av/短链解析
- 优先取 CC/AI 字幕；没有字幕再下载音频，用 faster-whisper 转写
- ffmpeg 抽关键帧（默认 6 张，可配到 12 张）
- 本地/相册视频同样支持
- 结果按视频 ID 缓存到 `data/video/*.json`，默认 7 天

### 2. 时间戳总结

`_summarize_video`：

- 字幕按 `[MM:SS]` 保留时间戳
- 关键帧分批交给视觉模型，**多批并行**，失败隔离
- 汇总成“这是什么视频 + 3–6 个带时间戳的要点 + 画面 + 感受”
- 不编造字幕和画面里没有的内容

### 3. 视频笔记

`video_notes.py`：

- 保存标题、UP、来源、时长、摘要、时间戳要点、字幕长度、关键帧数
- 同一视频重复看会更新，不会堆重复条目
- 文件：`data/video/notes.json`，最多保留 300 条
- 公开 http 视频的要点会同步写入世界记忆，主题为 `视频：<标题>`

### 4. 命令

```text
看视频 https://www.bilibili.com/video/BV...
视频 https://...              # 同上
视频笔记
忘记视频 关键词
```

B 站分享卡、引用视频、直接发视频文件也会触发。

## 配置

```json
{
  "video_enabled": true,
  "video_max_minutes": 30,
  "video_max_frames": 6,
  "video_asr_model": "small",
  "video_asr_language": "",
  "video_cache_days": 7,
  "bilibili_sessdata": ""
}
```

- `video_max_minutes`：超过上限直接拒绝，避免下载过长视频
- `video_max_frames`：关键帧数量，越多视觉 token 越高
- `video_asr_model`：`tiny` / `base` / `small`；CPU 上 small 较慢
- `bilibili_sessdata`：可选，用于需要登录态的字幕/视频

## 边界

- 只处理公开视频和用户主动发来的本地视频
- 不登录他人账号、不绕过付费墙、不抓隐私
- 字幕/画面不足时明确说“没拿到”，不假装看过
- 视频要点进入世界记忆后，可以用 `世界记忆` 查看、`忘记世界` 删除

## 下一步

- 视频章节切分与“跳转到某分钟”的卡片
- 多视频对比
- 4070 Ti 到位后把 ASR 换成本地 GPU，并接 Qwen3-TTS 做视频旁白
