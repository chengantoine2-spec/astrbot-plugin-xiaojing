# 安全策略

## 支持范围

当前维护 1.x 版本。发现安全问题请优先通过 GitHub 的 **Security Advisories** 私下报告，不要先开公开 issue。

## 请不要公开这些内容

- `data/config.json`：含 owner QQ、群号、NapCat token
- `data/netease.enc`：DPAPI 加密的网易云登录态
- `data/preferences.json`、`data/memory/`、`data/diary/`：聊天记忆与日记
- 任何 `api-key.txt`、`.env`、访问令牌、Cookie
- 带 QQ 号、群号、IP、token 的完整日志

如果日志里出现敏感信息，请先打码再贴到 issue。

## 部署建议

- 使用测试账号或小号运行机器人，避免主账号被风控。
- NapCat 的 HTTP/WS 端口不要直接暴露到公网；建议只监听 `127.0.0.1`，或通过防火墙/反向代理限制来源。
- 不要把 `data/` 目录提交到 Git。
- 定期轮换 NapCat token 与模型 API Key。
- 网易云 Cookie 使用 Windows DPAPI 加密，只能被当前 Windows 用户解密；换机器需要重新绑定。
