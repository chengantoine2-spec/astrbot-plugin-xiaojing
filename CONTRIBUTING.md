# 贡献指南

感谢你愿意改进小鲸。提交前请先确认：

## 不要提交

- `data/config.json`
- `data/netease.enc`
- `data/preferences.json`、`data/memory/`、`data/diary/`
- 任何 token、Cookie、API Key、QQ 号、群号、IP
- 带个人信息的日志或截图

提交前跑一次：

```powershell
git status
git diff --cached
```

## 代码

- Python 3.10+
- 保持现有文件结构，避免引入重型依赖
- 修改后至少跑一次语法检查：

```powershell
& "<AstrBot>\backend\python\python.exe" -m py_compile *.py
```

- 涉及聊天、点歌、日报的改动，请在 PR 里说明测试方式与结果

## 问题反馈

请附：

- 操作系统与 AstrBot / NapCat 版本
- 复现步骤
- 相关日志（先打码 QQ、群号、token、Cookie）

安全问题请走 [SECURITY.md](SECURITY.md)，不要开公开 issue。
