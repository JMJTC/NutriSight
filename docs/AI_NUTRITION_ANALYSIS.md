# AI 营养分析功能开发文档

## 功能概述

接入 AI 大语言模型（OpenAI 兼容接口），为食智眸系统提供智能营养分析能力。支持三种场景：
- **识别后即时分析**：上传食物图片识别后，AI 自动分析营养结构
- **历史饮食建议**：根据近期识别记录，AI 分析饮食趋势并给出改善建议
- **独立 AI 营养顾问**：自由对话式营养咨询

用户可自行配置 API Key、模型和 API 地址，支持 DeepSeek、通义千问、GLM、GPT 等所有 OpenAI 兼容接口的模型。

---

## 后端架构

```
app/
├── services/ai/                  # AI 核心服务层
│   ├── __init__.py
│   ├── client.py                 # OpenAI 兼容 HTTP 客户端
│   ├── prompts.py                # 提示词模板（3 套场景）
│   ├── streaming.py              # SSE 流式响应生成器
│   └── service.py                # AI 业务编排层
├── api/v1/ai/                    # AI 路由层
│   ├── __init__.py
│   └── ai.py                     # 7 个 API 端点
├── schemas/ai.py                 # AI 请求/响应 Pydantic 模型
├── utils/crypto.py               # API Key 加密工具
├── models/admin.py               # User 模型新增 AI 字段
```

### 组件职责

| 组件 | 职责 | 对外接口 |
|------|------|----------|
| `client.py` | 封装 httpx 异步调用 OpenAI 兼容 API，支持流式/非流式 | `AiClient.chat()`, `chat_stream()`, `test_connection()` |
| `prompts.py` | 管理 3 套系统提示词，注入结构化 JSON 上下文 | `build_analysis_prompt()`, `build_history_recommendation_prompt()`, `build_chat_system_prompt()` |
| `streaming.py` | 将上游 SSE 流转换为 FastAPI StreamingResponse | `create_streaming_response(user_id, scenario, **kwargs)` |
| `service.py` | 组装 context → 调 client → 持久化结果 | `AiService.analyze_record()`, `chat()`, `test_connection()` 等 |

### 数据流

```
前端 fetch SSE
    ↓
POST /api/v1/ai/chat/stream  (ai.py)
    ↓
create_streaming_response()  (streaming.py)
    ↓ _build_messages() → prompts.py 组装 system prompt
    ↓ 读取 User.api_key → crypto.decrypt_api_key()
    ↓
ai_client.chat_stream()  (client.py)
    ↓ httpx.AsyncClient.stream("POST", openai_url)
    ↓
yield token → JSON 序列化 → SSE text/event-stream → 前端逐字渲染
```

### API 端点

```
PUT  /api/v1/base/profile/ai-config      保存用户 AI 配置（API Key/模型/地址）
GET  /api/v1/base/profile/ai-config      获取配置（API Key 脱敏显示）

POST /api/v1/ai/analyze/record/{id}      识别记录分析（非流式）
POST /api/v1/ai/analyze/record/{id}/stream 识别记录分析（SSE 流式）
POST /api/v1/ai/analyze/history          历史饮食分析（非流式）
POST /api/v1/ai/analyze/history/stream   历史饮食分析（SSE 流式）
POST /api/v1/ai/chat                     营养对话（非流式）
POST /api/v1/ai/chat/stream              营养对话（SSE 流式）
POST /api/v1/ai/test                     测试 AI 连接
```

### 认证

所有 `/api/v1/ai/*` 端点使用 `DependAuth`，从 JWT Token 解析用户身份，再从 `User` 表读取该用户加密存储的 API Key。

---

## 前端架构

```
web/src/
├── components/ai/
│   ├── AiStreamRenderer.vue     # Markdown 流式内容渲染器
│   ├── AiChatPanel.vue          # 聊天面板（消息列表 + 输入框 + SSE 流读取）
│   └── AiConfigForm.vue         # API Key / 模型 / 地址配置表单
├── views/food/
│   ├── ai-advisor/index.vue     # AI 营养顾问独立页面
│   ├── recognition/index.vue    # 识别页（新增 AI 分析卡片）
│   ├── recognition/useFoodRecognition.js  # 识别 composable（新增 AI 分析逻辑）
│   └── history/index.vue        # 历史详情弹窗（规则建议 → 流式 AI）
├── views/profile/index.vue      # 个人资料页（新增 AI 配置选项卡）
└── api/index.js                 # 前端 API 层（新增 9 个 AI 方法）
```

### 流式读取实现

```javascript
// AiChatPanel.vue 核心逻辑
const response = await fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'token': getToken() },
  body: JSON.stringify({ messages, context })
})
const reader = response.body.getReader()
const decoder = new TextDecoder()
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  // 解析 SSE 格式 data: {"type":"token","content":"..."}
  // 逐 token 追加到显示内容
}
```

---

## 修改文件清单

### 新建文件（13 个）

| 文件 | 说明 |
|------|------|
| `app/services/ai/__init__.py` | AI 服务包 |
| `app/services/ai/client.py` | OpenAI 兼容 HTTP 客户端 |
| `app/services/ai/prompts.py` | 提示词模板 |
| `app/services/ai/streaming.py` | SSE 流式工具 |
| `app/services/ai/service.py` | AI 业务编排 |
| `app/api/v1/ai/__init__.py` | AI 路由包 |
| `app/api/v1/ai/ai.py` | AI API 路由 |
| `app/schemas/ai.py` | AI Pydantic 模型 |
| `app/utils/crypto.py` | API Key 加密工具 |
| `web/src/components/ai/AiStreamRenderer.vue` | 流式内容渲染 |
| `web/src/components/ai/AiChatPanel.vue` | 聊天面板 |
| `web/src/components/ai/AiConfigForm.vue` | AI 配置表单 |
| `web/src/views/food/ai-advisor/index.vue` | AI 顾问页面 |

### 修改文件（8 个）

| 文件 | 变更内容 |
|------|----------|
| `app/models/admin.py` | User 新增 `api_key`、`ai_model`、`ai_base_url` 字段 |
| `app/api/v1/__init__.py` | 注册 `ai_router`（前缀 `/ai`） |
| `app/api/v1/base/base.py` | 新增 `GET/PUT /profile/ai-config` 端点；`userinfo` 返回 `has_api_key` |
| `app/settings/config.py` | 新增 `AI_DEFAULT_MODEL`、`AI_DEFAULT_BASE_URL` |
| `app/schemas/users.py` | BaseUser/UserSelfUpdate 新增 AI 配置字段 |
| `app/core/middlewares.py` | 审计日志跳过 `text/event-stream` 响应 |
| `app/core/init_app.py` | 新增 AI 顾问菜单种子数据 |
| `web/src/api/index.js` | 新增 9 个 AI API 方法 |
| `web/src/views/profile/index.vue` | 新增"AI 配置"选项卡 |
| `web/src/views/food/history/index.vue` | 历史详情改为流式 AI 建议 |
| `web/src/views/food/recognition/index.vue` | 识别结果下方新增 AI 智能分析 |
| `web/src/views/food/recognition/useFoodRecognition.js` | 新增 AI 流式分析逻辑 |
| `web/src/router/routes/index.js` | 新增 AI 顾问页面路由 |

### 新增依赖

- **后端**：无新增（`httpx` 已在依赖中）
- **前端**：`markdown-it`（Markdown 渲染）

---

## 后续扩展指南

### 1. 添加新的 AI 模型

只需修改用户配置即可，无需改代码。支持的模型：

- **DeepSeek**: `deepseek-chat`, `deepseek-reasoner`
- **通义千问**: `qwen-turbo`, `qwen-plus`, `qwen-max`（Base URL: `https://dashscope.aliyuncs.com/compatible-mode`）
- **智谱 GLM**: `glm-4-flash`, `glm-4-plus`（Base URL: `https://open.bigmodel.cn/api/paas`）
- **Moonshot**: `moonshot-v1-8k`（Base URL: `https://api.moonshot.cn`）
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`（Base URL: `https://api.openai.com`）

### 2. 添加新的 AI 提供商接口格式（非 OpenAI 兼容）

如需接入 Anthropic Claude、Google Gemini 等非 OpenAI 格式的 API：

1. 在 `app/services/ai/client.py` 中新增 `AnthropicClient` 或 `GeminiClient` 类
2. 实现相同的接口方法：`chat()`, `chat_stream()`
3. 在 `app/services/ai/service.py` 的 `_get_user_ai_config()` 返回 provider 类型
4. 根据 provider 类型路由到不同客户端

```python
# 扩展示例
class AnthropicClient:
    async def chat_stream(self, messages, api_key, model=None):
        # Anthropic Messages API 实现
        ...

class GeminiClient:
    async def chat_stream(self, messages, api_key, model=None):
        # Google Gemini API 实现
        ...
```

### 3. 自定义提示词

编辑 `app/services/ai/prompts.py` 中的 3 个函数：

- `build_analysis_prompt()` — 识别分析提示词
- `build_history_recommendation_prompt()` — 历史建议提示词
- `build_chat_system_prompt()` — 对话系统提示词

提示词使用 Python f-string，通过 `json.dumps()` 注入结构化数据。

### 4. 添加新的 AI 场景

1. 在 `app/services/ai/prompts.py` 新增提示词构建函数
2. 在 `app/services/ai/streaming.py` 的 `_build_messages()` 新增场景分支
3. 在 `app/services/ai/service.py` 新增业务方法
4. 在 `app/api/v1/ai/ai.py` 新增路由端点

### 5. 切换加密方式

当前使用 XOR + Base64（keyed by SECRET_KEY）。如需更强的加密：

1. 修改 `app/utils/crypto.py` 中的 `encrypt_api_key()` 和 `decrypt_api_key()`
2. 推荐方案：`cryptography` 库的 Fernet 对称加密
   ```python
   from cryptography.fernet import Fernet
   # pip install cryptography
   ```

### 6. 前端流式渲染增强

- 在 `AiStreamRenderer.vue` 中可集成 `highlight.js` 实现代码高亮
- 在 `AiChatPanel.vue` 中可增加消息操作（复制、重新生成、点赞/踩）
- 上下文面板可扩展为显示关联的识别记录缩略图

### 7. 速率限制增强

当前未实现限流（设计中提到 10 req/min）。可在 `app/services/ai/service.py` 或中间件层添加：

```python
# 使用 aioredis 或内存字典实现滑动窗口限流
from collections import defaultdict
import time

_rate_limits = defaultdict(list)

def check_rate_limit(user_id: int, max_req: int = 10, window: int = 60) -> bool:
    now = time.time()
    _rate_limits[user_id] = [t for t in _rate_limits[user_id] if now - t < window]
    if len(_rate_limits[user_id]) >= max_req:
        return False
    _rate_limits[user_id].append(now)
    return True
```

---

# AI Nutrition Analysis Feature Documentation

## Overview

Integrates AI large language models (OpenAI-compatible API) into the Smart Food Eye (食智眸) system for intelligent nutritional analysis across three scenarios:

- **Post-Recognition Analysis**: After food image recognition, AI automatically analyzes nutritional structure
- **History-Based Recommendations**: Analyzes dietary trends from recent records and provides improvement suggestions
- **AI Nutrition Advisor**: Free-form conversational nutrition consultation

Users configure their own API Key, model, and base URL. Supports all OpenAI-compatible models including DeepSeek, Qwen, GLM, GPT, etc.

---

## Backend Architecture

```
app/
├── services/ai/                  # AI Core Service Layer
│   ├── __init__.py
│   ├── client.py                 # OpenAI-compatible HTTP client
│   ├── prompts.py                # Prompt templates (3 scenarios)
│   ├── streaming.py              # SSE streaming response generator
│   └── service.py                # AI business orchestration
├── api/v1/ai/                    # AI Route Layer
│   ├── __init__.py
│   └── ai.py                     # 7 API endpoints
├── schemas/ai.py                 # AI request/response Pydantic models
├── utils/crypto.py               # API Key encryption utility
├── models/admin.py               # User model: added AI fields
```

### Component Responsibilities

| Component | Responsibility | Public Interface |
|-----------|---------------|------------------|
| `client.py` | httpx async OpenAI-compatible API calls (stream & non-stream) | `AiClient.chat()`, `chat_stream()`, `test_connection()` |
| `prompts.py` | 3 system prompt templates with structured JSON context injection | `build_analysis_prompt()`, `build_history_recommendation_prompt()`, `build_chat_system_prompt()` |
| `streaming.py` | Converts upstream SSE stream to FastAPI StreamingResponse | `create_streaming_response(user_id, scenario, **kwargs)` |
| `service.py` | Assembles context → calls client → persists results | `AiService.analyze_record()`, `chat()`, `test_connection()` etc. |

### Data Flow

```
Frontend fetch (SSE)
    ↓
POST /api/v1/ai/chat/stream  (ai.py)
    ↓
create_streaming_response()  (streaming.py)
    ↓ _build_messages() → prompts.py assembles system prompt
    ↓ Read User.api_key → crypto.decrypt_api_key()
    ↓
ai_client.chat_stream()  (client.py)
    ↓ httpx.AsyncClient.stream("POST", openai_url)
    ↓
yield token → JSON serialize → SSE text/event-stream → frontend renders
```

### API Endpoints

```
PUT  /api/v1/base/profile/ai-config      Save user AI config (API Key/model/URL)
GET  /api/v1/base/profile/ai-config      Get config (API Key masked)

POST /api/v1/ai/analyze/record/{id}      Record analysis (non-stream)
POST /api/v1/ai/analyze/record/{id}/stream Record analysis (SSE stream)
POST /api/v1/ai/analyze/history          History analysis (non-stream)
POST /api/v1/ai/analyze/history/stream   History analysis (SSE stream)
POST /api/v1/ai/chat                     Nutrition chat (non-stream)
POST /api/v1/ai/chat/stream              Nutrition chat (SSE stream)
POST /api/v1/ai/test                     Test AI connectivity
```

### Authentication

All `/api/v1/ai/*` endpoints use `DependAuth`, resolving user identity from JWT token, then reading the user's encrypted API Key from the `User` table.

---

## Frontend Architecture

```
web/src/
├── components/ai/
│   ├── AiStreamRenderer.vue     # Markdown streaming content renderer
│   ├── AiChatPanel.vue          # Chat panel (messages + input + SSE reader)
│   └── AiConfigForm.vue         # API Key / model / URL config form
├── views/food/
│   ├── ai-advisor/index.vue     # AI Advisor standalone page
│   ├── recognition/index.vue    # Recognition page (added AI analysis card)
│   ├── recognition/useFoodRecognition.js  # Recognition composable (added AI logic)
│   └── history/index.vue        # History detail modal (rule-based → streaming AI)
├── views/profile/index.vue      # Profile page (added AI config tab)
└── api/index.js                 # Frontend API layer (added 9 AI methods)
```

### Streaming Implementation

```javascript
// AiChatPanel.vue core logic
const response = await fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'token': getToken() },
  body: JSON.stringify({ messages, context })
})
const reader = response.body.getReader()
const decoder = new TextDecoder()
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  // Parse SSE format: data: {"type":"token","content":"..."}
  // Append tokens to display content incrementally
}
```

---

## File Change Summary

### New Files (13)

| File | Description |
|------|-------------|
| `app/services/ai/__init__.py` | AI service package |
| `app/services/ai/client.py` | OpenAI-compatible HTTP client |
| `app/services/ai/prompts.py` | Prompt templates |
| `app/services/ai/streaming.py` | SSE streaming utility |
| `app/services/ai/service.py` | AI business orchestration |
| `app/api/v1/ai/__init__.py` | AI route package |
| `app/api/v1/ai/ai.py` | AI API route handlers |
| `app/schemas/ai.py` | AI Pydantic models |
| `app/utils/crypto.py` | API Key encryption utility |
| `web/src/components/ai/AiStreamRenderer.vue` | Streaming content renderer |
| `web/src/components/ai/AiChatPanel.vue` | Chat panel |
| `web/src/components/ai/AiConfigForm.vue` | AI config form |
| `web/src/views/food/ai-advisor/index.vue` | AI advisor page |

### Modified Files (13)

| File | Changes |
|------|---------|
| `app/models/admin.py` | Added `api_key`, `ai_model`, `ai_base_url` to User |
| `app/api/v1/__init__.py` | Registered `ai_router` with `/ai` prefix |
| `app/api/v1/base/base.py` | Added `GET/PUT /profile/ai-config`; `userinfo` returns `has_api_key` |
| `app/settings/config.py` | Added `AI_DEFAULT_MODEL`, `AI_DEFAULT_BASE_URL` |
| `app/schemas/users.py` | Added AI config fields to BaseUser / UserSelfUpdate |
| `app/core/middlewares.py` | Skip `text/event-stream` in audit log |
| `app/core/init_app.py` | Added AI advisor menu seed |
| `web/src/api/index.js` | Added 9 AI API methods |
| `web/src/views/profile/index.vue` | Added "AI Config" tab |
| `web/src/views/food/history/index.vue` | Replaced rule-based tips with streaming AI |
| `web/src/views/food/recognition/index.vue` | Added AI analysis card below results |
| `web/src/views/food/recognition/useFoodRecognition.js` | Added AI streaming logic |
| `web/src/router/routes/index.js` | Added AI advisor page route |

### New Dependencies

- **Backend**: None (`httpx` already in deps)
- **Frontend**: `markdown-it` (Markdown rendering)

---

## Extension Guide

### 1. Adding New AI Models

No code changes needed — users configure via the AI Config UI. Supported models:

- **DeepSeek**: `deepseek-chat`, `deepseek-reasoner`
- **Qwen (Alibaba)**: `qwen-turbo`, `qwen-plus`, `qwen-max` (Base URL: `https://dashscope.aliyuncs.com/compatible-mode`)
- **GLM (Zhipu)**: `glm-4-flash`, `glm-4-plus` (Base URL: `https://open.bigmodel.cn/api/paas`)
- **Moonshot**: `moonshot-v1-8k` (Base URL: `https://api.moonshot.cn`)
- **OpenAI**: `gpt-4o`, `gpt-4o-mini` (Base URL: `https://api.openai.com`)

### 2. Adding Non-OpenAI API Providers

For APIs like Anthropic Claude or Google Gemini that don't follow the OpenAI format:

1. Create a new client class in `app/services/ai/client.py` (e.g., `AnthropicClient`, `GeminiClient`)
2. Implement the same interface methods: `chat()`, `chat_stream()`
3. Add provider routing in `app/services/ai/service.py` `_get_user_ai_config()`
4. Route to the appropriate client based on provider type

```python
# Extension example
class AnthropicClient:
    async def chat_stream(self, messages, api_key, model=None):
        # Anthropic Messages API implementation
        ...

class GeminiClient:
    async def chat_stream(self, messages, api_key, model=None):
        # Google Gemini API implementation
        ...
```

### 3. Customizing Prompts

Edit the 3 functions in `app/services/ai/prompts.py`:

- `build_analysis_prompt()` — recognition analysis prompt
- `build_history_recommendation_prompt()` — history recommendation prompt
- `build_chat_system_prompt()` — chat system prompt

Prompts use Python f-strings with `json.dumps()` for structured data injection.

### 4. Adding New AI Scenarios

1. Add a new prompt builder in `app/services/ai/prompts.py`
2. Add a new scenario branch in `app/services/ai/streaming.py` `_build_messages()`
3. Add a new service method in `app/services/ai/service.py`
4. Add a new route in `app/api/v1/ai/ai.py`

### 5. Strengthening Encryption

Current: XOR + Base64 (keyed by SECRET_KEY). For stronger encryption:

1. Modify `encrypt_api_key()` and `decrypt_api_key()` in `app/utils/crypto.py`
2. Recommended: `cryptography` library's Fernet symmetric encryption
   ```python
   from cryptography.fernet import Fernet
   # pip install cryptography
   ```

### 6. Frontend Enhancements

- Integrate `highlight.js` in `AiStreamRenderer.vue` for code highlighting
- Add message actions in `AiChatPanel.vue` (copy, regenerate, thumbs up/down)
- Expand context sidebar to show associated record thumbnails

### 7. Rate Limiting (Not Yet Implemented)

Designed as 10 req/min per user. To implement:

```python
from collections import defaultdict
import time

_rate_limits = defaultdict(list)

def check_rate_limit(user_id: int, max_req: int = 10, window: int = 60) -> bool:
    now = time.time()
    _rate_limits[user_id] = [t for t in _rate_limits[user_id] if now - t < window]
    if len(_rate_limits[user_id]) >= max_req:
        return False
    _rate_limits[user_id].append(now)
    return True
```
