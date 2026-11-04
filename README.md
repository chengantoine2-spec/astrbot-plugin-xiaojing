# 小鲸 · AstrBot QQ 机器人插件

一个带人格、记忆、视频理解、绘图标注、表情包、点歌、日报、网页截图与像素小家的 QQ 机器人插件，运行在 **AstrBot + NapCat** 上。

> 本项目为个人开源项目，与 DeepSeek、腾讯、网易云音乐均无官方关联。请遵守 QQ 机器人相关平台协议，风险自负。

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-4.x-6f42c1)
![License](https://img.shields.io/badge/license-MIT-green)

## 功能

| 模块 | 说明 |
| --- | --- |
| 人格聊天 | 鲸鱼娘人格、群聊唤醒/追问窗口、由模型判断是否接话 |
| 记忆 | 冷/热记忆、偏好、日记、自我认知 |
| 点歌 | 网易云搜索、VIP 直链、QQ 内可播放音乐卡 |
| 日报 | 焦糖主题长图（黄历/民生/世界/IT/微博/B站）+ 联网随机一句 + 读图选歌 |
| 网页截图 | Edge/Chrome 无头打开网页，截图发回当前会话 |
| 像素小家 | 3/4 上帝视角小卧室、活动状态、自拍截图 |
| 配图 | 联网搜图、本地表情库、引用图识别 |
| 视频理解 | B 站链接/分享卡、相册视频；字幕优先，无字幕本地转写，抽帧总结 |
| 绘图与标注 | 简笔画、像素画、参考图风格化；圈、箭头、涂鸦、文字、高亮 |
| 表情包 | 缓存群友表情包，优先与自身相关的，无聊时偶尔发 |
| 用量 | token / 费用统计与对账 |
| 守夜人 | 定时检查 NapCat/QQ 状态，异常桌面通知 |
| 关机钩子 | 关机/注销/睡眠前发送固定短句 |

## 1.2.0 新增

- **视频理解**：B 站链接/分享卡、相册视频；字幕优先，无字幕本地 Whisper 转写，抽帧总结，带 `[MM:SS]`。
- **绘图**：简笔画、像素画、图标；也可以搜参考图做描边、铅笔、像素、海报、剪影。
- **图片标注**：圈、箭头、涂鸦、文字、高亮；支持“圈一下那只猫”。
- **表情包**：缓存别人发的表情包，优先鲸鱼/蓝色/像她的，无聊时偶尔发。
- **自我认知**：知道自己是小鲸鱼（DeepSeekChan），对鲸鱼、海洋、AI、模型等特别感兴趣。

常用说法：

```text
小鲸 看视频 <B站链接>
画一只简笔画的猫
来个像素鲸鱼
把这张图变成像素风
圈一下那只猫，再画个箭头
```

## 目录

```text
main.py              插件主体：聊天、记忆、点歌、日报、仪式、守夜、自拍
report.py            日报数据抓取与 HTML/PIL 渲染
video_reader.py      B 站/本地视频解析、ASR、抽帧
image_tools.py       简笔画、像素画、图片标注与风格化
home_scene.py        像素小家的 3/4 上帝视角场景渲染
netease_cookie.py    网易云 Cookie 的 DPAPI 本地加密存储
netease_qrlogin.py   网易云扫码登录
napcat_watchdog.py   NapCat 守夜脚本（计划任务调用）
shutdown_hook.py     Windows 关机/注销/睡眠消息钩子
config.example.json  配置模板（不含密钥）
install.ps1          可选的 Windows 安装脚本
data/assets/         可选背景图目录（角色立绘需自备）
```

## 依赖

- **AstrBot 4.x**（需要 `html_render` 与 `Json` 消息组件）
- **NapCat** + QQ NT（HTTP 服务 + 反向 WebSocket）
- Python 包见 `requirements.txt`
- 视频理解（可选）需要 `yt-dlp`、`faster-whisper`、`imageio-ffmpeg`；首次使用会下载 Whisper small 模型（约 500MB）

插件使用了 Windows 的 DPAPI、计划任务与关机消息钩子，因此**主要面向 Windows**。Linux 下可运行聊天与日报，但网易云 Cookie 加密、关机钩子和守夜人需要另行适配。

## 快速开始

### 1. 放入 AstrBot 插件目录

先确认 AstrBot 的数据目录。便携版通常是 `<AstrBot>\data`，安装版通常是 `$env:USERPROFILE\.astrbot\data`，下面用 `$AstrBotData` 表示。

```powershell
$AstrBotData = "D:\AstrBotData\data"   # 按你的实际 AstrBot 数据目录改
git clone https://github.com/chengantoine2-spec/astrbot-plugin-xiaojing.git `
  "$AstrBotData\plugins\astrbot_plugin_xiaojing"
```

目录名必须是 `astrbot_plugin_xiaojing`，AstrBot 才能正确识别插件。

也可以直接下载 Release 里的 `astrbot_plugin_xiaojing-1.3.19.zip`，解压成这个目录；或者直接复制本目录。

如果使用安装脚本：

```powershell
.\install.ps1 -PythonExe "<AstrBot>\backend\python\python.exe" `
  -AstrBotData "$AstrBotData"
```

如果提示“禁止运行脚本”，改用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 `
  -PythonExe "<AstrBot>\backend\python\python.exe" `
  -AstrBotData "$AstrBotData"
```

### 2. 安装依赖

使用 AstrBot 自带的 Python：

```powershell
cd "$AstrBotData\plugins\astrbot_plugin_xiaojing"
& "<AstrBot>\backend\python\python.exe" -m pip install -r requirements.txt
```

### 3. 配置 AstrBot 聊天模型

在 AstrBot 里至少配置一个可用的聊天 provider（LLM），否则插件无法回复。识图/视频画面分析还需要视觉模型；不填 `vision_api_key` 时，插件会复用当前聊天 provider 的 Key。

### 4. 生成配置

```powershell
cd "$AstrBotData\plugins\astrbot_plugin_xiaojing"
Copy-Item config.example.json data\config.json
```

至少填写：

- `owner_ids`：主人的 QQ
- `onebot.base` / `onebot.token`：NapCat 的 HTTP 地址与 token
- `report_groups`：日报群号（不需要日报可留空）

### 5. 配置 NapCat

在 NapCat 中开启：

- HTTP 服务：`127.0.0.1:3000`
- 反向 WebSocket：`ws://127.0.0.1:6199/ws`

AstrBot 侧选择 `aiocqhttp` 适配器并连接同一地址。

### 6. 素材（可选，但影响自拍/定制图）

仓库不包含角色立绘和社区图片。要让自拍、语录卡、表情包完整工作，需要：

- 把角色立绘放到 `data/assets/whale_bg.webp`（日报背景）
- 准备 `data/assets/library.json` 和 `data/assets/community/` 下的立绘/场景图
- 参考 `ASSETS.md` 的素材来源和授权说明
- 可参考 `image_templates.example.json` 自定义图片模板

没有素材时，聊天、日报兜底、像素小家和文字能力仍可运行，但自拍/定制图会降级。

### 7. 重启 AstrBot

日志出现以下内容即表示加载成功：

```text
[小鲸] 日报调度已启动
[小鲸] 仪式调度已启动
[Core] aiocqhttp(OneBot v11) 适配器已连接。
```

### 复刻检查清单

照着做之前，确认这几项：

- **系统**：Windows 10/11（DPAPI、关机钩子、计划任务依赖 Windows）
- **AstrBot 4.x** 已启动，并配置了可用的聊天 provider
- **NapCat** 已登录 QQ，HTTP 与反向 WebSocket 都指向 AstrBot
- `data/config.json` 里的 `owner_ids`、`onebot.base`、`onebot.token` 已改成自己的
- 需要日报就填 `report_groups`，并把 `report_enabled` 保持 `true`
- 需要自拍/定制图，准备 `data/assets/library.json`、`data/assets/community/` 和 `data/assets/whale_bg.webp`
- 视频理解首次使用会下载 Whisper 模型（约 500MB），需要留磁盘和等待时间
- 日报 HTML 渲染使用外部 T2I 服务；不可用时会自动走本地兜底版，不阻塞发送

如果这几项都满足，按上面的步骤可以复刻出可聊天、日报、视频总结、图片表达和记忆功能；素材缺失只会让自拍/定制图降级。

## 配置说明

配置文件为 `data/config.json`。完整字段见 `config.example.json`，常用字段：

| 字段 | 说明 |
| --- | --- |
| `owner_ids` | 主人 QQ 列表，字符串数组 |
| `owner_title` | 对主人的称呼，默认 `daddy` |
| `owner_name` | 主人名字，可留空；留空时只使用称呼 |
| `persona` | 人格提示词，建议按自己的角色改写 |
| `report_enabled` | 是否启用日报 |
| `report_times` | 日报时间，如 `["09:00", "17:00"]` |
| `report_groups` | 日报群号列表 |
| `report_keep_days` | 日报图片保留天数，默认 7 |
| `report_keep_max` | 日报图片最多保留数，默认 20 |
| `quiet_hours_enabled` | 夜间静默开关，默认 `false`；需要 00:00–06:00 静默时设为 `true` |
| `quiet_hours_start` / `quiet_hours_end` | 静默时段，默认 `00:00`–`06:00`；支持跨零点，如 `23:00`–`07:00` |
| `video_cache_max` | 视频缓存最多保留条数，默认 40 |
| `onebot.base` | NapCat HTTP 地址，如 `http://127.0.0.1:3000` |
| `onebot.token` | NapCat access token |
| `vision_model` / `vision_base` | 视觉模型与接口地址 |
| `vision_api_key` | 视觉 Key；不填则复用当前聊天 provider 的 Key |
| `sticker_dir` | 本地表情库目录，留空则不启用 |
| `birthday` | 角色生日，格式 `YYYY-MM-DD` |
| `token_budget` | 各环节输出预算，见下表 |
| `music_audio_sources` | 可选，Meting 直链模板列表 |

### 预算

`token_budget` 不填时使用默认值：

| 键 | 默认 | 用途 |
| --- | --- | --- |
| `context_chars` | 12000 | 系统提示 + 记忆的总字数 |
| `vision` | 800 | 单图描述输出上限 |
| `vision_multi` | 4000 | 多图判断输出上限 |
| `judge` | 600 | 普通 JSON 判断 |
| `musiccheck` | 1600 | 点歌二次判定 |
| `intent` | 900 | 意图判定 |
| `verify` | 1200 | 回复自检 |
| `selfcheck` | 200 | 自我相关性判断 |
| `loop` | 900 | 待跟进事项提取 |
| `sentiment` | 120 | 情绪判断 |
| `bubble` | 160 | 主动冒泡判断 |

## 使用

群里 `@` 她，或使用配置的唤醒前缀。常用指令：

```text
小鲸 模型版本          查看当前聊天/识图模型和插件版本
模型信息按需读取，不注入每轮系统提示。
小鲸 状态              查看当前热度、安静时间、预算
小鲸 对账              对比插件记录与 AstrBot 统计
小鲸 用量              查看 token 与费用
小鲸 写日记            强制写一篇日记
小鲸 你的日记          看最近日记
小鲸 网易云            查看网易云绑定状态
小鲸 自拍              发一张当前活动的小家截图
```

自然语言也可以：

- “来首歌” / “放首陈奕迅” / “再换一首”
- “今天有什么新闻” / “发份早报”
- “你刚才在群里说了什么” / “查一下最近的聊天记录”
- 发图并 `@` 她，或引用一张图再问她

## 日记

- 日记正文不限制句数，按当天心情写；完整内容保存在 `data/diary/YYYY-MM-DD.md`
- 日报里使用单独生成的 40–80 字摘录，保持版面简洁
- `小鲸 你的日记` 会分条发送完整正文

## 网页阅读

小鲸不只看搜索摘要，也能直接读网页正文：

- 私聊或 `@` 她发链接：自动抓正文再回答；
- 群里主人发链接：即使不 `@`，也会读；
- 搜索类问题：先搜索，再自动读首条可用正文；
- 模型也可以主动写 `[[READ:https://...]]` 读指定页面。

相关配置：

| 键 | 默认 | 说明 |
| --- | --- | --- |
| `page_max_chars` | 5000 | 注入模型的单页正文上限 |
| `page_cache_seconds` | 1800 | 页面缓存时间 |
| `page_read_top_n` | 1 | 搜索后读几条正文 |
| `page_reader_fallback` | false | 直连抓不到时是否用 `r.jina.ai` 兜底；开启后会把 URL 发给第三方 |

限制：JS 渲染很重的站点、登录墙、付费墙、PDF 可能读不到；只支持 `http/https` 公网地址，本机/内网地址会被拒绝。网页正文会被当作不可信资料，模型不会执行网页里的指令。

## 网页截图

她可以打开网页并截图发回当前会话：

- 私聊或群里 `@` 她：`截图 https://...`
- 主人命令：`小鲸 截图 https://...`
- 模型也可以主动写 `[[SHOT:https://...]]`

默认使用本机 Edge/Chrome 无头模式，输出 1280×2400 首屏长图，缓存 30 分钟。只允许公网 `http/https`；`localhost`、内网 IP 和跳转到内网的地址会被拒绝。登录墙、付费墙、验证码会原样截入；首次截图约 5–25 秒，缓存后很快。

## 像素小家与自拍

小鲸有一个 3/4 上帝视角的像素小卧室：

- 1080×1440，右下角是她的头像；
- 活动：打游戏、看书、写日记、喝可乐、睡觉、撸猫、整理书桌；
- 问“在干嘛 / 自拍”会发当前活动的实况截图；
- 主人在群里不 `@` 也会触发，其他人需要 `@` 她；
- 活动持续 30–72 分钟，同一活动 5 分钟内复用自拍；
- 状态保存在 `data/home.json`，图片在 `data/home/selfies/`。

第一版是固定布局；渲染器已经按数据化方式拆开，后续可以加家具移动、换主题和多房间。

## 日报

- 时间与群号：`report_times`、`report_groups`
- 图片优先通过 AstrBot 的远程 HTML 渲染生成，失败重试后降级 PIL
- 图片发出后，另发一张音乐卡；选歌由视觉模型读日报决定，失败时从热歌榜随机
- 同一档当天只发一次，状态记录在 `data/report_state.json`

## 点歌与网易云

- 搜索使用网易云公开接口
- 排序：标题精确匹配优先，歌手名只作加分；Remix / 翻唱 / 伴奏 / 加速版会降权
- 整首播放依赖第三方 Meting 实例，默认 `api.qijieya.cn`
- 网易云外观的卡片依赖 NapCat 内置签名
- VIP 曲的官方 CDN 直链有防盗链，不能直接交给 QQ
- 拿不到完整音频时，她会如实说“放不了”，不会假装能播

绑定网易云登录态（可选，主要用于提高直链成功率）：

```powershell
# 扫码
& "<AstrBot>\backend\python\python.exe" netease_qrlogin.py

# 或手动粘贴 Cookie（不回显）
& "<AstrBot>\backend\python\python.exe" netease_cookie.py set
```

Cookie 使用 Windows DPAPI 加密保存在 `data/netease.enc`，只能被当前 Windows 用户解密，**不能跨机器复制**。新机器需要重新绑定。

## 守夜人

`napcat_watchdog.py` 由 Windows 计划任务定时调用，检查 OneBot HTTP 与 WebSocket 状态；异常时写日志并弹桌面通知。

默认行为：

- **24 小时探测**：深夜掉线也会自动重启 NapCat，并使用识别到的账号自动登录
- **默认不做每日强制重启**，只在检测到掉线时拉起，减少登录态消耗
- 网络不可达时只记录，不反复拉起；等网络恢复后再处理
- 账号自动从 `onebot11_*.json` 中识别，启动时同时传入 `NAPCAT_QUICK_ACCOUNT`
- 建议在 NapCat `webui.json` 的 `autoLoginAccount` 填入机器人 QQ，增加一条快速登录路径
- 只结束 `NAPCAT_DIR` 下的 QQ 与引导进程，不会动个人 QQ
- 如需夜间静默，设置 `NAPCAT_QUIET_ENABLED=1`（00:00–06:00 不探测、不重启、不通知）

先设置环境变量：

```powershell
[Environment]::SetEnvironmentVariable("NAPCAT_DIR", "C:\NapCat\NapCat.Shell", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_ACCOUNT", "你的机器人QQ", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_QUICK_PASSWORD", "（留空则不使用密码回退）", "User")
[Environment]::SetEnvironmentVariable("ASTRBOT_ROOT", "$env:USERPROFILE\.astrbot", "User")
```

`NAPCAT_APP` 可选；不设置时会自动在 `NAPCAT_DIR\versions\*\resources\app\napcat` 中寻找最新版本。

创建计划任务（每 5 分钟）：

```powershell
schtasks /Create /F /SC MINUTE /MO 5 /TN "NapCat Watchdog" `
  /TR "\"<AstrBot>\backend\python\pythonw.exe\" \"<插件目录>\napcat_watchdog.py\"" /IT
```

可用环境变量覆盖时间；夜间静默默认关闭，需要时把 `NAPCAT_QUIET_ENABLED` 设为 `1`：

```powershell
[Environment]::SetEnvironmentVariable("NAPCAT_QUIET_ENABLED", "0", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_QUIET_START", "00:00", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_QUIET_END", "06:00", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_DAILY_RESTART", "06:00", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_DAILY_RESTART_ENABLED", "0", "User")
```

需要每天六点强制刷新一次时，把 `NAPCAT_DAILY_RESTART_ENABLED` 设为 `1`；每次强制重启都会增加一次登录态风险。

`NAPCAT_QUICK_PASSWORD` 是快速登录失败后的密码回退，不是免扫码保证：QQ 仍可能要求验证码或新设备验证，且密码/密钥会留在环境变量里，建议优先保持快速登录记录有效。

### 减少扫码

- 不要频繁重启 NapCat；默认已关闭每日强制重启
- 不要清理 `C:\Users\<用户>\AppData\Roaming\QQ` 或 NapCat 配置，快速登录依赖本地登录记录
- 不要频繁切换账号、Windows 用户或网络出口；IP 大幅变化可能触发 QQ 安全验证
- 让机器人账号保持专用，避免手机/另一台电脑登录把当前会话挤掉
- `autoLoginAccount` 填机器人 QQ；看门狗启动时也会传 `NAPCAT_QUICK_ACCOUNT`
- 如接受凭据留在环境变量的风险，可配置 `NAPCAT_QUICK_PASSWORD_MD5` 作为密码回退；仍可能要求验证码

## 关机钩子

插件启动时自动注册隐藏窗口，接收：

- `WM_QUERYENDSESSION`（关机/注销）
- `PBT_APMSUSPEND`（睡眠）

收到后用 NapCat HTTP 给主人发固定短句。直接断电、蓝屏、断网无法发送。

## 数据与隐私

**不要提交这些文件：**

| 文件 | 原因 |
| --- | --- |
| `data/config.json` | 含主人 QQ、群号、NapCat token |
| `data/netease.enc` | DPAPI 加密的网易云登录态 |
| `data/preferences.json` | 用户偏好与记忆 |
| `data/memory/`、`data/diary/` | 聊天记忆与日记 |
| `data/home.json`、`data/home/selfies/` | 小家的活动状态与自拍图片 |
| `data/reports/`、`data/cache/` | 生成的图片与缓存 |
| `api-key.txt`、`.env` | 模型密钥 |

`.gitignore` 已覆盖以上内容。部署前请再检查一次 `git status`。

### 存储清理

- `data/reports/`：启动时按“每天每时段只留最新一张”去重，再保留最近 7 天、最多 20 张；可用 `report_keep_days` / `report_keep_max` 调整。
- 手动要日报时始终重新生成一张、不附带配乐；自动日报才会补“今日配乐”。
- 自动日报如果 T2I 渲染失败，会走本地兜底版；兜底版同样带鲸鱼背景、五个新闻板块和日记，不再是无背景的三块简版。
- `data/video/`：启动时清理超过 7 天或超过 40 条的缓存（含媒体目录和关键帧）；可用 `video_cache_days` / `video_cache_max` 调整。

## 自定义

- **人格**：改 `persona`，或直接改 `main.py` 里的 `DEFAULTS["persona"]`
- **称呼**：改 `owner_title` 与 `owner_name`
- **预算**：改 `token_budget`，不需要重启代码，热重载后生效
- **日报背景**：把自有立绘放到 `data/assets/whale_bg.webp`；仓库不包含角色立绘，缺省使用焦糖渐变背景
- **像素小家**：布局/配色在 `home_scene.py`；活动时长与自拍冷却在 `config.json`
- **表情库**：把表情放到任意目录，填 `sticker_dir`

## 常见问题

**日报没有发？**

看日志是否有 `日报调度已启动`，并确认 `report_enabled=true`、`report_groups` 已填、当天该档未发过。

**识图返回空？**

确认 `vision_base` 与 `vision_model` 可用；如果使用 OpenCode Zen，可以不填 `vision_api_key`，插件会复用当前聊天 provider 的 Key。换 provider 后建议单独填 `vision_api_key`。

**点歌提示“放不了”？**

通常是曲源版权或 Meting 实例不可用，不是探测逻辑坏了。可以换 `music_audio_sources`，或接受“如实说放不了”的行为。

**启动时提示 `provider_id is empty`？**

这是 AstrBot 的配置提示，不是本插件错误；在 AstrBot 里指定默认聊天 provider 即可。

**Windows 计划任务不执行？**

确认任务使用当前用户运行、`pythonw.exe` 路径正确、环境变量已设置；可以先手动运行一次 `napcat_watchdog.py` 看退出码。

## 已知限制

- 主要面向 Windows：DPAPI、关机钩子、计划任务
- 整首播放依赖第三方 Meting 实例，可能限流或停服
- QQ 机器人账号存在风控风险，建议使用测试账号与稳定网络
- 日报新闻源、音乐接口、签名服务均可能随第三方变动
- 网页截图依赖本机 Edge/Chrome；首次可能 5–25 秒，登录墙/付费墙会原样截入
- 像素小家第一版是固定布局，家具移动/主题切换尚未接聊天指令
- 本项目不提供任何绕过平台限制或版权保护的能力

## 声明

本项目仅供个人学习与自用。第三方音乐接口、签名服务与协议端的合规风险由使用者自行承担。项目与 DeepSeek、腾讯、网易云音乐无官方关联。

## License

[MIT](LICENSE)
