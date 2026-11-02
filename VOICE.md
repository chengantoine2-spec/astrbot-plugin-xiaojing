# 语音与角色音色（Voice）

## 当前推荐

### 首选：Qwen3-TTS

**云端最快可用：`Chelsie`**

- 官方音色描述：**二次元虚拟女友**
- 适合：软萌、年轻、亲近、略带二次元感
- 语言：中文、英语、日语、韩语等
- 接入：阿里云百炼 / DashScope，需要 API Key

**本地 4070 Ti：Qwen3-TTS 1.7B VoiceDesign / CustomVoice**

- 开源，Apache-2.0
- 1.7B，4070 Ti 12GB 足够
- 支持 **VoiceDesign**：用文字描述设计专属声线，不需要克隆真人
- 支持 **Voice Design → Clone**：先设计一段参考音，再固定成可复用音色
- 支持流式，官方标称首包延迟可低至 97ms
- 可用 `qwen-tts-demo` 起 WebUI，或用 vLLM-Omni 的 OpenAI 兼容 `/audio/speech`

### 备选

| 方案 | 特点 | 适合 |
| --- | --- | --- |
| CosyVoice 2 `longfeifei_v2` | 甜美娇气女；0.5B 低显存 | 想快速试音、低配本地 |
| CosyVoice 2 `longyingling` | 温和共情女 | 更温柔、陪伴感 |
| IndexTTS2 | 情感控制强，8GB 显存可跑 | 想要明显情绪起伏 |
| GPT-SoVITS v2Pro | 1 分钟参考音克隆，社区模型多 | 已有授权参考音，想做独特声线 |
| Qwen3-TTS `Vivian` | 明亮、轻微小脾气少女音 | 不想用云、也不想训练 |
| Qwen3-TTS `Serena` | 温暖柔和少女音 | 更安静、更治愈 |

## DeepSeekChan 专属声线设计

给 Qwen3-TTS VoiceDesign 的参考描述：

```text
年轻女性，18-20 岁，音色清亮偏软，带一点海风般的通透感；
中高音，语速稍慢，句尾轻微上扬；
软萌但不幼稚，认真时吐字清晰、节奏干脆；
偶尔带一点中二得意和撒娇；
不要成熟御姐，不要过度萝莉，不要播音腔。
```

这段描述对应她的人设：Q 版鲸鱼娘、软萌、会撒娇、但遇到正事会认真。

## 接入方式

### 1. 当前默认：Windows SAPI

```json
"tts_provider": "sapi",
"tts_sapi_voice": "Microsoft Huihui Desktop"
```

离线、免费、无需 API；音色偏朗读腔，作为兜底。

### 2. 4070 Ti 本地：Qwen3-TTS + vLLM-Omni（OpenAI 兼容）

安装并启动服务后，把配置改成：

```json
"tts_provider": "openai",
"tts_base": "http://127.0.0.1:8000/v1",
"tts_key": "local",
"tts_model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
"tts_api_voice": "Vivian",
"tts_language": "Chinese",
"tts_fallback_sapi": true
```

如果服务不可用，会自动回退 SAPI，不会静默失败。

### 3. 云端 Qwen3-TTS `Chelsie`

需要阿里云百炼 / DashScope API Key。当前插件预留 `openai` 兼容接口；如果 DashScope 端点不是 OpenAI 格式，需要再加一个 `dashscope` provider。

## 命令

```text
音色                 # 查看当前音色方案
语音 先生，晚上好。   # 生成并发送 QQ 语音
说一句 今天也辛苦啦。
念一下 该休息了。
```

## 已知限制

- QQ 语音通常走 Silk/AMR；当前用 `Record(file=wav)`，NapCat 已实测可发送 WAV。
- SAPI 音色不是角色声线；等 4070 Ti 到位后切 Qwen3-TTS。
- 语音不参与图片预算，但同样不应刷屏。
