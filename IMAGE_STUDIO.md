# 图片工坊（Image Studio）

小鲸鱼的长期定制图能力。模板放在：

```text
data/assets/image_templates.json
```

代码在 `image_studio.py`。模板是运行时读取的，**增删模板和换素材不需要重启**；只有改 `image_studio.py` / `main.py` 的代码才需要重启后端。

## 命令

```text
定制图 今天也要好好吃饭
语录卡 今天也要好好吃饭
表情包 困了|先睡一会儿
成就卡 连续聊天 7 天|小鲸鱼把这件事记下来了
改图 今天也在写日记|——小鲸鱼      # 需要引用/附带一张图
加字 今天的风好大                  # 需要引用/附带一张图
```

- `表情包` 的文字用 `|` 分隔上/下字幕；只有一段时放到底部。
- `成就卡` 用 `|` 分隔标题/副标题。
- `改图` / `加字` 会取当前消息或引用图；没有图会提示先发图。

## 模型标记

系统提示里注册了：

```text
[[CARD:模板|文字]]
```

模板可省略，默认 `quote`；文字不超过 60 字。例如：

```text
[[CARD:meme|开心|转圈圈]]
[[CARD:quote|今天也在好好生活]]
[[CARD:achievement|连续聊天 7 天|小鲸鱼记住了]]
```

模型会在轻松聊天时偶尔主动用一次，不会在严肃/技术/报错话题里刷图。

## 模板类型

| kind | 用途 | 主要字段 |
| --- | --- | --- |
| `quote` | 语录卡 | `character`、`accent`、`bubble`、`text` |
| `meme` | 表情包字幕 | `character`（无图时使用） |
| `achievement` | 成就卡 | `character`、`accent` |
| `edit_text` | 改图加字 | 无角色字段，使用用户图片 |

## 新增模板

1. 把背景/角色图放到 `data/assets/community/` 或 `data/assets/templates/`。
2. 在 `image_templates.json` 里加一条：

```json
{
  "id": "my_card",
  "name": "我的卡片",
  "kind": "quote",
  "character": "assets/community/q_c49_halfbody.jpg",
  "accent": "#6EA8FF",
  "bubble": "#F7F3EA",
  "text": "#1B2540",
  "keywords": ["我的卡", "专属卡"]
}
```

3. 用 `定制图` 或 `[[CARD:my_card|文字]]` 调用。
4. 模板路径相对 `data/`，解析时会拒绝越出 `data/` 的路径。

## 素材来源与许可

- 角色参考：`TreapGoGo/deepseek-whale-girl`（MIT License）
- 扩展素材：`AATINF/deepseek-whale-girl-assets`（AI 生成，使用/再分发请署名）
- 详细署名见 `ASSETS.md` 与 `data/assets/CREDITS.md`

素材只在本地使用，不随公开仓库分发。

## 新增模板（2026-11-02）

| kind | 命令 | 文字格式 |
| --- | --- | --- |
| `list` | `清单卡` / `要点卡` | `标题|条目1|条目2` |
| `compare` | `对比卡` / `对比图` | `左标题|左内容|右标题|右内容` |
| `timeline` | `时间线` / `日程卡` | `标题|09:00:事件|12:00:事件` |

模型标记同样可用：

```text
[[CARD:list|这周要做的事|清日报|补看门狗]]
[[CARD:compare|旧方案|文字描述|新方案|一张图]]
[[CARD:timeline|今天的进度|09:00:起床|12:00:做图]]
```

## 读图 / OCR

```text
读图
提取文字
```

需要当前消息或引用图。模型也可以写 `[[OCR]]` 主动读图。

## 图片预算

主动/会话图片默认：

```json
"image_budget_per_10min": 4,
"image_cooldown_seconds": 45,
"image_dedupe_minutes": 30
```

截图、日报、自拍、显式 `改图/定制图` 命令可通过 `force_image` 绕过。

## 反馈

发送记录与用户正负反馈写入 `data/image_feedback.json`；
模板目录会在提示词里显示 `反馈+N`，长期影响选型。

## 图片 2.0 命令（2026-11-02）

```text
对比这两张              # 两张图差异 + 并排对比图
裁剪 16:9               # 也支持 1:1 / 4:3 / 9:16 / 3:4
黑白 / 暖色 / 冷色 / 复古 / 锐化 / 模糊
拼图                    # 2-4 张
中间模糊 / 左边模糊 / 右边模糊 / 上面模糊 / 下面模糊
```

- `对比图` 仍是文字对比卡；`对比这两张` 才是看图对比。
- 编辑命令会取当前消息图、引用图或最近图。
- 图片预算/去重同样适用，显式编辑命令可绕过。
