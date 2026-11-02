# 语音（Voice）

离线 TTS，使用 Windows 自带 SAPI，不依赖云 API。

## 依赖

- Windows `System.Speech`
- 中文音色：`Microsoft Huihui Desktop`（当前机器已安装）
- `voice_tools.py`：生成 22.05kHz 单声道 WAV

## 命令

```text
语音 先生，晚上好，我是小鲸鱼。
说一句 今天也辛苦啦。
念一下 该休息了。
```

- 只走命令触发，不会自动把每条回复转成语音。
- 生成失败会自动回退文字，不会静默吞消息。
- 配置项：`"voice_enabled": true`

## 已知限制

- SAPI 音色偏“朗读腔”，不是角色声线；后续可接 FishAudio / Genie / Qwen TTS 做角色音色。
- QQ 语音通常走 Silk/AMR；当前通过 AstrBot `Record(file=wav)` 发送，若 NapCat 不接受 WAV，需要在发送前转码。
- 语音不参与图片预算；但同样受“不要刷屏”的总体节奏约束。
