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
