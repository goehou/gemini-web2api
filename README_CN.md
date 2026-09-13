# gemini-web2api

<p align="center">
  <img src="logo.png" width="200" alt="gemini-web2api logo">
</p>

[English](README.md)

将 Google Gemini 网页端转换为 OpenAI 兼容 API. 零成本, 跨平台, 单文件.

## 特性

- **可选密钥**: `api_keys` 为空时免密, 填入密钥后按 OpenAI Bearer Key 校验
- **OpenAI 兼容**: 直接替换 `/v1/chat/completions` 和 `/v1/models`
- **工具调用**: 完整的 Function Calling 支持 (OpenAI 格式)
- **多模型**: Flash (3.6), 扩展思考 (2万字+输出), Pro, Auto, Lite
- **思考深度**: 通过 `@think=N` 后缀调节 (0=最深, 4=最浅)
- **联网搜索**: 内置互联网访问 (Gemini 原生搜索能力)
- **跨平台**: 纯 Python, 仅一个可选依赖 (`httpx` 用于流式输出)
- **流式输出**: 基于 `httpx` 的 SSE Streaming 支持
- **Codex CLI**: Responses API (`/v1/responses`) 兼容 OpenAI Codex
- **Gemini CLI**: Google 原生 API (`/v1beta/models`) 兼容 Gemini CLI

## 快速开始

```bash
pip install httpx
python gemini_web2api.py
```

服务启动在 `http://localhost:8081/v1`.

## 双端口链路 (匿名 + Cookie)

可以同时跑两个实例, 各占一个端口: 一条匿名路, 一条带 cookie 路.

建两个配置文件 (参考 `.env.example`),

`.env.anon` (无鉴权):

```
PORT=8081
```

`.env.cookie` (带 cookie):

```
PORT=8082
COOKIE_FILE=cookie.txt
```

一条命令启动两个端口:

```bash
python start_all.py
```

| 端口 | 配置文件 | 路由行为 |
|------|---------|---------|
| 8081 | `.env.anon` | 匿名, 所有模型路由到 Flash-Lite |
| 8082 | `.env.cookie` | cookie 认证, 模型类别真实生效 |

客户端指向 8081 走匿名, 指向 8082 走认证, 互不干扰. 启动 banner 会显示 `Env file:` 和 `Cookie: yes/none (anonymous)`, 可确认实例身份.

也可以分别启动:

```bash
python -m gemini_web2api --env-file .env.anon
python -m gemini_web2api --env-file .env.cookie
```

> 注意: `COOKIE_FILE` 指向的文件不存在时, 实例会静默以匿名模式运行, 不会报错. Cookie 配置见下文.

## 客户端配置

### Cherry Studio / ChatBox / 任何 OpenAI 兼容客户端

| 字段 | 值 |
|------|-----|
| Base URL | `http://localhost:8081/v1` |
| API Key | `config.json` 中的任意 `api_keys`；未配置时随便填 |
| Model | `gemini-3.5-flash-thinking` |

### curl

```bash
curl http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-key" \
  -d '{"model":"gemini-3.5-flash","messages":[{"role":"user","content":"你好!"}]}'
```

### OpenAI Python SDK

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8081/v1", api_key="sk-your-key")
resp = client.chat.completions.create(
    model="gemini-3.5-flash-thinking",
    messages=[{"role": "user", "content": "解释量子计算"}]
)
print(resp.choices[0].message.content)
```

### Gemini CLI

```bash
export GEMINI_API_KEY=none
export GOOGLE_GEMINI_BASE_URL=http://localhost:8081
gemini
```

支持 Google 原生 API 端点:
- `GET /v1beta/models` — 模型列表
- `POST /v1beta/models/{model}:generateContent` — 非流式生成
- `POST /v1beta/models/{model}:streamGenerateContent` — 流式生成 (SSE)

## 可用模型

| 模型 | 说明 | 输出量 |
|------|------|--------|
| `gemini-3.8-flash` | 全能模型 (最新) | ~1.2万字 |
| `gemini-3.6-flash` | 全能模型 | ~1.2万字 |
| `gemini-3.5-flash` | gemini-3.6-flash 别名 | ~1.2万字 |
| `gemini-3.5-flash-thinking` | 扩展思考, 最长输出 | **~2万字** |
| `gemini-3.5-flash-thinking-lite` | 自适应思考深度 | ~1.5万字 |
| `gemini-3.1-pro` | 高级数学与代码 (需 cookie) | ~1.2万字 |
| `gemini-auto` | 自动选择模型 | 不定 |
| `gemini-flash-lite` | 最快响应, 轻量 | ~1万字 |

### 思考深度

在模型名后追加 `@think=N`:

```
gemini-3.5-flash-thinking@think=0   # 最深 (默认)
gemini-3.5-flash-thinking@think=2   # 中等
gemini-3.5-flash-thinking@think=4   # 最浅
```

## Cookie 配置 (详细)

### 为什么要配 Cookie

模型选择通过请求 payload 的 `[79]` 字段把"模型类别"发给 Gemini 服务端, 但**匿名请求下服务端会无视类别号, 所有模型统一路由到 Flash-Lite** (实测确认). 配置 cookie 后类别号才被服务端采用:

- `gemini-3.8-flash` / `gemini-3.6-flash` (FAST 类别) → 路由到账号 FAST 档位当前挂载的模型
- `gemini-3.1-pro` (PRO 类别) → 免费 Google 账号会静默回退到 Flash, 需要 **Gemini Advanced (付费订阅)** 才有真 Pro 路由
- 没有官方的无鉴权 API: Gemini API 免费层需要 Google 账号 + AI Studio 的 key, 匿名只有网页端的基础档

### 方式一: 仓库自带浏览器扩展 (推荐)

扩展一次性导出 cookie + SAPISID + XSRF token + gemini_bl, 比手动全:

1. Chrome 打开 `chrome://extensions` → 开启右上角**开发者模式** → **加载已解压的扩展程序** → 选择本仓库的 `gemini-cookie-sync-extension` 目录
2. 打开 [gemini.google.com/app](https://gemini.google.com/app), 登录 Google 账号, 刷新页面
3. 点扩展图标 → **Inspect session**, 确认显示:

   ```
   XSRF / SNlM0e: present
   gemini_bl / cfb2h: present
   ```

4. 点 **Export gemini-auth.json**, 得到包含 cookie、`sapisid`、`xsrf_token`、`gemini_bl`、`auth_user` 的完整认证文件
5. `config.json` 中设置 `"cookie_file": "gemini-auth.json"

> `gemini.google.com` 的 `bl` 版本号会随部署更新, 扩展导出的 `gemini_bl` 是当前值, 比手填更可靠.

### 方式二: 手动从 DevTools 提取

1. Chrome 访问 [gemini.google.com](https://gemini.google.com) 并登录, 按 **F12** 打开开发者工具
2. **Application (应用)** 标签 → 左侧 **Cookies** → `https://gemini.google.com`
3. 复制以下 cookie 的值:

   | Cookie | 作用 |
   |--------|------|
   | `SID` / `HSID` / `SSID` | Google 登录态 |
   | `APISID` / `SAPISID` | API 鉴权 (SAPISID 同时用于 sapisidhash) |
   | `__Secure-1PSID` | 会话凭证 |

4. 项目根目录创建 `cookie.txt`, JSON 格式:

```json
{"cookie": "SID=xxx; HSID=xxx; SSID=xxx; APISID=xxx; SAPISID=xxx; __Secure-1PSID=xxx", "sapisid": "SAPISID的值"}
```

或纯文本单行格式:

```
SID=xxx; HSID=xxx; SSID=xxx; APISID=xxx; SAPISID=xxx; __Secure-1PSID=xxx
```

启动方式:

```bash
python gemini_web2api.py --cookie-file cookie.txt
```

### 登录账号路径与 XSRF Token

如果已登录的 Gemini 页面 URL 带账号序号, 例如:

```
https://gemini.google.com/u/1/app/...
```

请把 `auth_user` 设置为该序号。登录态的 Gemini Web 请求还可能需要页面里的 XSRF token。该 token 在渲染后的 Gemini 页面源码中名为 `SNlM0e`; 在 `config.json` 中填入 `xsrf_token` 后, 服务会把它作为 `at` 表单字段提交。

示例:

```json
{
  "cookie_file": "/app/cookie.txt",
  "auth_user": "1",
  "xsrf_token": "AOOh0P...",
  "gemini_bl": "boq_assistant-bard-web-server_YYYYMMDD.xx_p0"
}
```

如果登录态请求返回 HTTP 400 且错误中包含 `xsrf`, 请刷新 Gemini Web 后更新 `xsrf_token`, 并确认 `auth_user` 与浏览器 URL 中的 `/u/<序号>/` 一致.

Pro 路由需要 **Gemini Advanced** (付费订阅). 免费 Google 账号的 cookie 可以登录认证, 但会静默回退到 Flash.

### 验证路由是否生效

启动带 cookie 的实例后发一条请求, 看服务日志:

```bash
curl http://localhost:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-key" \
  -d '{"model":"gemini-3.8-flash","messages":[{"role":"user","content":"hi"}]}'
```

服务日志会输出后端实际路由的模型名:

```
[xx:xx:xx] actual model from response: 3.X Flash
```

显示的就是 FAST 档位真实挂载的模型. 如果仍是 `3.5 Flash-Lite`, 检查 cookie 文件路径与登录态是否有效.

## 配置文件

在同目录创建 `config.json`:

```json
{
  "port": 8081,
  "host": "0.0.0.0",
  "retry_attempts": 3,
  "retry_delay_sec": 2,
  "request_timeout_sec": 180,
  "gemini_bl": "boq_assistant-bard-web-server_20260716.08_p0",
  "auth_user": null,
  "xsrf_token": null,
  "api_keys": ["sk-your-key"],
  "cookie_file": null,
  "proxy": null,
  "log_requests": true,
  "temporary_chats": false
}
```

将 `temporary_chats` 设置为 `true` 后，请求会使用 Gemini 网页版的临时聊天，
不会将对话保存在账号历史记录中。

`api_keys` 为空数组 `[]` 时不校验密钥；填入一个或多个密钥后, `/v1/*` 接口需要 `Authorization: Bearer <key>` 或 `x-api-key: <key>`.

### 上下文缓存

服务提供基于 SQLite 的本地上下文缓存。通过 `POST /v1/caches` 创建缓存，
然后在 Chat Completions 或 Responses 请求中传入 `cache_id`。开启
`auto_cache` 后，稳定的系统上下文和多轮请求中的历史对话会自动缓存。
缓存 Token 通过 `usage.prompt_tokens_details.cached_tokens` 估算返回；这是代理
侧统计，不是 Gemini 上游的计费数据。

## Docker 部署

```bash
cp config.example.json config.json
docker build -t gemini-web2api .
docker run -d --name gemini-web2api -p 8081:8081 -v ./config.json:/app/config.json gemini-web2api
```

或使用 Docker Compose:

```bash
cp config.example.json config.json
docker compose up -d
```

如需挂载 Cookie 文件:

```bash
docker run -d --name gemini-web2api -p 8081:8081 -v ./config.json:/app/config.json -v ./cookie.txt:/app/cookie.txt gemini-web2api
```

此时 `config.json` 中设置 `"cookie_file": "/app/cookie.txt"`.

> **注意**: 如果 Docker 默认 bridge 网络下出现空回复 (`content: null`), 请切换到 host 网络: `docker run --network host ...` 或在 compose 文件中添加 `network_mode: host`. 这是 Gemini 上游拒绝来自 Docker NAT IP 段的请求导致的.

## 代理配置

如果无法直接访问 `gemini.google.com` (连接超时), 需要配置代理:

**方式 1: 命令行参数**
```bash
python gemini_web2api.py --proxy http://127.0.0.1:7890
```

**方式 2: config.json**
```json
{"proxy": "http://127.0.0.1:7890"}
```

**方式 3: 环境变量** (自动检测)
```bash
set HTTPS_PROXY=http://127.0.0.1:7890
python gemini_web2api.py
```

支持 Clash, V2Ray, Shadowsocks 等任何 HTTP 代理.

## 图片输入

Chat Completions 和 Responses API 支持 OpenAI 风格的多模态消息。图片可以使用
HTTP(S) URL 或 base64 data URL:

```python
resp = client.chat.completions.create(
    model="gemini-3.6-flash",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图片"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}}
        ]
    }]
)
```

## 已知限制

- **图片上传可能需要 Cookie**: 多模态输入使用 Gemini 网页端图片上传接口。匿名上传失败时, 请配置 Gemini cookie。
- **Pro/Ultra 非真实路由**: 无付费订阅 cookie 时, `gemini-3.1-pro` 实际路由到 Flash 模型. "Pro" 只是 UI 偏好标签.
- **单轮对话**: 每次请求是独立对话, 多轮上下文通过在 prompt 中包含历史消息模拟.
- **频率限制**: Google 可能限制高频请求, server 会自动重试但持续高负载可能被封.

## 系统要求

- Python 3.8+
- `httpx` (`pip install httpx`) — 用于流式请求
- 需要能访问 `gemini.google.com` (部分地区需代理)

## 工作原理

逆向 Google Gemini 网页端的 StreamGenerate 协议, 将 OpenAI API 格式与 Gemini 内部 protobuf-like 格式互转. 模型选择通过请求 payload 的 `[79]` 字段控制, 映射自 Gemini 前端 JS 源码中的 `MODE_CATEGORY` 枚举.

## 致谢

- [linux.do](https://linux.do) 社区
- 开源 API 代理生态

## License

MIT
