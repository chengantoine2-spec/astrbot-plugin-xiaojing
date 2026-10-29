# 小鲸 · AstrBot QQ 机器人插件

一个带人格、记忆、点歌、日报与运维小工具的 QQ 机器人插件，运行在 **AstrBot + NapCat** 上。

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
| 配图 | 联网搜图、本地表情库、引用图识别 |
| 用量 | token / 费用统计与对账 |
| 守夜人 | 定时检查 NapCat/QQ 状态，异常桌面通知 |
| 关机钩子 | 关机/注销/睡眠前发送固定短句 |

## 目录

```text
main.py              插件主体：聊天、记忆、点歌、日报、仪式、守夜
report.py            日报数据抓取与 HTML/PIL 渲染
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

插件使用了 Windows 的 DPAPI、计划任务与关机消息钩子，因此**主要面向 Windows**。Linux 下可运行聊天与日报，但网易云 Cookie 加密、关机钩子和守夜人需要另行适配。

## 快速开始

### 1. 放入 AstrBot 插件目录

```powershell
git clone https://github.com/<your-name>/astrbot-plugin-xiaojing.git `
  "$env:USERPROFILE\.astrbot\data\plugins\astrbot_plugin_xiaojing"
```

目录名必须是 `astrbot_plugin_xiaojing`，AstrBot 才能正确识别插件。

也可以直接复制本目录，或运行：

```powershell
.\install.ps1 -PythonExe "<AstrBot>\backend\python\python.exe"
```

### 2. 安装依赖

使用 AstrBot 自带的 Python：

```powershell
& "<AstrBot>\backend\python\python.exe" -m pip install -r requirements.txt
```

### 3. 生成配置

```powershell
Copy-Item config.example.json data\config.json
```

至少填写：

- `owner_ids`：主人的 QQ
- `onebot.base` / `onebot.token`：NapCat 的 HTTP 地址与 token
- `report_groups`：日报群号（不需要日报可留空）

### 4. 配置 NapCat

在 NapCat 中开启：

- HTTP 服务：`127.0.0.1:3000`
- 反向 WebSocket：`ws://127.0.0.1:6199/ws`

AstrBot 侧选择 `aiocqhttp` 适配器并连接同一地址。

### 5. 重启 AstrBot

日志出现以下内容即表示加载成功：

```text
[小鲸] 日报调度已启动
[小鲸] 仪式调度已启动
[Core] aiocqhttp(OneBot v11) 适配器已连接。
```

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
小鲸 状态              查看当前热度、安静时间、预算
小鲸 对账              对比插件记录与 AstrBot 统计
小鲸 用量              查看 token 与费用
小鲸 写日记            强制写一篇日记
小鲸 你的日记          看最近日记
小鲸 网易云            查看网易云绑定状态
```

自然语言也可以：

- “来首歌” / “放首陈奕迅” / “再换一首”
- “今天有什么新闻” / “发份早报”
- “你刚才在群里说了什么” / “查一下最近的聊天记录”
- 发图并 `@` 她，或引用一张图再问她

## 日报

- 时间与群号：`report_times`、`report_groups`
- 图片优先通过 AstrBot 的远程 HTML 渲染生成，失败重试后降级 PIL
- 图片发出后，另发一张音乐卡；选歌由视觉模型读日报决定，失败时从热歌榜随机
- 同一档当天只发一次，状态记录在 `data/report_state.json`

## 点歌与网易云

- 搜索使用网易云公开接口
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

先设置环境变量：

```powershell
[Environment]::SetEnvironmentVariable("NAPCAT_DIR", "C:\NapCat\NapCat.Shell", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_ACCOUNT", "你的机器人QQ", "User")
[Environment]::SetEnvironmentVariable("NAPCAT_QUICK_PASSWORD", "快速登录密码（可留空）", "User")
[Environment]::SetEnvironmentVariable("ASTRBOT_ROOT", "$env:USERPROFILE\.astrbot", "User")
```

`NAPCAT_APP` 可选；不设置时会自动在 `NAPCAT_DIR\versions\*\resources\app\napcat` 中寻找最新版本。

创建计划任务（每 5 分钟）：

```powershell
schtasks /Create /F /SC MINUTE /MO 5 /TN "NapCat Watchdog" `
  /TR "\"<AstrBot>\backend\python\pythonw.exe\" \"<插件目录>\napcat_watchdog.py\"" /IT
```

`NAPCAT_QUICK_PASSWORD` 留空时只通知、不自动登录。

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
| `data/reports/`、`data/cache/` | 生成的图片与缓存 |
| `api-key.txt`、`.env` | 模型密钥 |

`.gitignore` 已覆盖以上内容。部署前请再检查一次 `git status`。

## 自定义

- **人格**：改 `persona`，或直接改 `main.py` 里的 `DEFAULTS["persona"]`
- **称呼**：改 `owner_title` 与 `owner_name`
- **预算**：改 `token_budget`，不需要重启代码，热重载后生效
- **日报背景**：把自有立绘放到 `data/assets/whale_bg.webp`；仓库不包含角色立绘，缺省使用焦糖渐变背景
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
- 本项目不提供任何绕过平台限制或版权保护的能力

## 声明

本项目仅供个人学习与自用。第三方音乐接口、签名服务与协议端的合规风险由使用者自行承担。项目与 DeepSeek、腾讯、网易云音乐无官方关联。

## License

[MIT](LICENSE)
