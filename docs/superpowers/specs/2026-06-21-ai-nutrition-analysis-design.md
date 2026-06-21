# AI Nutrition Analysis — Design Spec

**Date:** 2026-06-21
**Branch:** food_recognition (new feature branch to be created)
**Status:** Draft

## Overview

Integrate AI large language models (LLM) via OpenAI-compatible API to provide intelligent nutritional analysis and dietary recommendations. The existing rule-based recommendation system is replaced/enhanced with LLM-generated content across three scenarios: post-recognition instant analysis, history-based dietary advice, and an independent nutrition chat advisor.

## Goals

- Support all OpenAI-compatible API models (DeepSeek, Qwen, GLM, Moonshot, etc.)
- Each user configures their own API Key, model, and base URL
- Streaming-first output (SSE) with non-streaming fallback
- Full AI enhancement: recognition analysis, history recommendation, free-form nutrition chat

## Backend Architecture

### File Structure (new files only)

```
app/services/ai/
├── __init__.py
├── client.py            # OpenAI-compatible HTTP client (httpx async)
├── prompts.py           # System prompt templates (3 scenarios)
├── streaming.py         # SSE stream response generator
└── service.py           # AI orchestration layer

app/api/v1/ai/
├── __init__.py
└── ai.py                # AI route handlers (/api/v1/ai/*)

app/schemas/ai.py        # AI request/response Pydantic schemas
```

### Model Changes

**User table (add to `app/models/admin.py`):**
- `api_key` (TextField, nullable) — user's own AI API Key, encrypted at rest
- `ai_model` (CharField, default="deepseek-chat") — model name
- `ai_base_url` (CharField, nullable) — custom API base URL

### Components

| Component | Responsibility |
|-----------|---------------|
| `client.py` | httpx async OpenAI-compatible API calls, stream and non-stream modes |
| `prompts.py` | 3 system prompt templates (record analysis, history recommendation, general chat), injects structured JSON context |
| `streaming.py` | `async def sse_generator()` — converts upstream SSE chunks to FastAPI StreamingResponse |
| `service.py` | Selects prompt by scenario, assembles messages + context, calls client, persists results to NutritionRecommendation |

## API Endpoints

### User AI Config (extends existing profile routes)

```
PUT  /base/profile/ai-config     # Save api_key, ai_model, ai_base_url
GET  /base/profile/ai-config     # Get config (api_key masked: first 4 + last 4 chars)
```

### AI Endpoints (new router at `/api/v1/ai`)

```
# Record analysis
POST /ai/analyze/record/{record_id}           # Non-streaming
POST /ai/analyze/record/{record_id}/stream     # SSE streaming

# Free-form chat
POST /ai/chat                                  # Non-streaming
POST /ai/chat/stream                           # SSE streaming

# Utility
GET  /ai/models                                # List available models
POST /ai/test                                  # Test API connectivity
```

### Auth

All `/ai/*` endpoints use `DependAuth`. API Key is read from the authenticated user's record.

### Request/Response

```python
# POST /ai/chat
{ "messages": [{"role": "user", "content": "..."}], "context": "record_id: 123" }

# SSE stream
data: {"type": "token", "content": "根据"}
data: {"type": "token", "content": "您的"}
...
data: {"type": "done", "record_id": 456}

# Non-stream response
{ "content": "full response...", "record_id": 456 }
```

## Prompt Strategy

Three system prompts, all returning Chinese:

1. **Record analysis** — Injects: food list + nutrition summary + user body metrics (BMI, targets). Instructs: act as registered dietitian, analyze meal structure, point out highlights and improvements, ≤300 chars.

2. **History recommendation** — Injects: recent records list + trend data. Instructs: act as health advisor, analyze dietary pattern trends, give long-term improvement advice.

3. **General chat** — Injects: conversation history. Instructs: act as professional nutrition consultant, cover food nutrition, diet planning, weight management, special dietary needs (diabetes, hypertension). Accurate, friendly.

Each prompt injects structured JSON to ground the AI on real data.

## Streaming Design (SSE)

```
Frontend fetch + ReadableStream
    → POST /ai/chat/stream
    → FastAPI StreamingResponse (async generator)
    → ai_client.chat_stream() — httpx.AsyncClient.stream("POST", ...)
    → OpenAI-compatible upstream SSE
    → yield per-token → JSON serialize → frontend renders
```

On `[DONE]`, the full response is saved to `NutritionRecommendation` table.

## Frontend

### Pages Changed

| Page | Change |
|------|--------|
| Profile (`views/profile/`) | New "AI Config" card: API Key input (masked), model dropdown, base URL input, connectivity test button |
| Recognition result | After YOLO detection, auto-trigger streaming AI analysis below results |
| History detail modal | Replace rule-based tips with real streaming AI output |
| AI Advisor (new `views/food/ai-advisor/`) | Independent chat page: chat panel on left, collapsible context sidebar on right |

### New Components

```
web/src/components/ai/
├── AiChatPanel.vue       # Message list + input box
├── AiStreamRenderer.vue  # Streaming Markdown renderer
└── AiConfigForm.vue      # API Key config form
```

### Key Frontend Details

- Streaming read: `fetch()` + `response.body.getReader()` for SSE parsing
- Markdown rendering: `markdown-it` for AI responses
- Context display: sidebar shows "Associated: Record #123", switchable
- Error UX: unconfigured key → guide button to profile; invalid key → inline error; connection lost → retry button

## Error Handling

| Scenario | Response |
|----------|----------|
| No API Key configured | 400 + "请在个人资料中配置 AI API Key" |
| Invalid API Key | 401 → "API Key 无效，请检查" |
| Model not found | 404 → "模型不可用，请更换模型" |
| API timeout (30s) | 408 → "AI 服务响应超时" |
| Stream interrupted | Frontend detects early close, shows partial + retry |
| Rate limit (10 req/min/user) | 429 → "请求过于频繁，请稍后重试" |
| Upstream non-stream | Client detects, degrades to batch render |

## Security

- API Key storage: AES reversible encryption (reuse project's argon2 utilities pattern)
- Log sanitization: API Key truncated to first 4 + last 4 in all logs
- Rate limiting: 10 requests per minute per user
- Response cap: 4096 token max, prevent runaway consumption
