# AI Nutrition Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate AI LLM (OpenAI-compatible API) for nutritional analysis: post-recognition analysis, history-based advice, and free-form nutrition chat.

**Architecture:** Independent `app/services/ai/` package with OpenAI-compatible HTTP client, prompt templates, SSE streaming. New `/api/v1/ai/*` routes. User-level API Key in User model. Frontend: streaming chat panel, AI advisor page, modifications to food pages.

**Tech Stack:** httpx (already in deps), FastAPI StreamingResponse + SSE, Vue 3 + Naive UI, markdown-it (new frontend dep)

---

## File Map

**Create (backend):**
- `app/services/ai/__init__.py`, `client.py`, `prompts.py`, `streaming.py`, `service.py`
- `app/api/v1/ai/__init__.py`, `ai.py`
- `app/schemas/ai.py`
- `app/utils/crypto.py`

**Modify (backend):**
- `app/models/admin.py` — add `api_key`, `ai_model`, `ai_base_url` to User
- `app/api/v1/__init__.py` — register ai_router
- `app/api/v1/base/base.py` — add AI config GET/PUT + has_api_key in userinfo
- `app/settings/config.py` — add AI default settings

**Create (frontend):**
- `web/src/components/ai/AiStreamRenderer.vue`, `AiChatPanel.vue`, `AiConfigForm.vue`
- `web/src/views/food/ai-advisor/index.vue`

**Modify (frontend):**
- `web/src/api/index.js` — AI API calls
- `web/src/views/profile/index.vue` — AI config tab
- `web/src/views/food/history/index.vue` — streaming AI in detail
- `web/src/views/food/recognition/index.vue` — instant AI analysis

---

### Task 1: Create AI client (`app/services/ai/`)

**Files:** Create `app/services/ai/__init__.py`, `app/services/ai/client.py`

- [ ] **Step 1: Write `client.py`**

```python
import json
from typing import AsyncIterator, Dict, List, Optional
import httpx
from app.log import logger
from app.settings.config import settings

TIMEOUT = 60.0
MAX_TOKENS = 4096


class AiClient:

    @staticmethod
    def _sanitize_key(api_key: str) -> str:
        if len(api_key) <= 8: return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"

    @staticmethod
    def _headers(api_key: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    @staticmethod
    async def chat(messages: List[Dict[str, str]], api_key: str,
                   base_url: Optional[str] = None, model: Optional[str] = None) -> Dict:
        url = (base_url or settings.AI_DEFAULT_BASE_URL).rstrip("/") + "/v1/chat/completions"
        model = model or settings.AI_DEFAULT_MODEL
        payload = {"model": model, "messages": messages, "max_tokens": MAX_TOKENS, "stream": False}
        logger.info(f"AI request: model={model}, key={AiClient._sanitize_key(api_key)}")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(url, headers=AiClient._headers(api_key), json=payload)
            result = response.json()
            if response.status_code != 200:
                error_msg = result.get("error", {}).get("message", response.text)
                raise AiClient._map_error(response.status_code, error_msg)
            return {"content": result["choices"][0]["message"]["content"]}

    @staticmethod
    async def chat_stream(messages: List[Dict[str, str]], api_key: str,
                          base_url: Optional[str] = None, model: Optional[str] = None) -> AsyncIterator[str]:
        url = (base_url or settings.AI_DEFAULT_BASE_URL).rstrip("/") + "/v1/chat/completions"
        model = model or settings.AI_DEFAULT_MODEL
        payload = {"model": model, "messages": messages, "max_tokens": MAX_TOKENS, "stream": True}
        logger.info(f"AI stream: model={model}, key={AiClient._sanitize_key(api_key)}")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            async with client.stream("POST", url, headers=AiClient._headers(api_key), json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise AiClient._map_error(resp.status_code, body.decode())
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]": break
                        try:
                            data = json.loads(data_str)
                            token = data["choices"][0].get("delta", {}).get("content", "")
                            if token: yield token
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    @staticmethod
    async def test_connection(api_key: str, base_url: Optional[str] = None,
                              model: Optional[str] = None) -> Dict:
        url = (base_url or settings.AI_DEFAULT_BASE_URL).rstrip("/") + "/v1/chat/completions"
        model = model or settings.AI_DEFAULT_MODEL
        payload = {"model": model, "messages": [{"role": "user", "content": "Hi"}],
                   "max_tokens": 5, "stream": False}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=AiClient._headers(api_key), json=payload)
            if resp.status_code == 200: return {"status": "ok", "model": model}
            err = resp.json().get("error", {}).get("message", "Unknown error")
            raise AiClient._map_error(resp.status_code, err)

    @staticmethod
    def _map_error(status_code: int, message: str) -> Exception:
        from app.core.exceptions import CustomException
        if status_code == 401: return CustomException(message="API Key 无效，请检查后重试", code=401)
        elif status_code == 404: return CustomException(message="模型不可用，请检查模型名称", code=404)
        elif status_code == 429: return CustomException(message="请求过于频繁，请稍后重试", code=429)
        elif status_code >= 500: return CustomException(message=f"AI 服务暂时不可用: {message}", code=502)
        return CustomException(message=f"AI 请求失败: {message}", code=400)


ai_client = AiClient()
```

- [ ] **Step 2: Commit**
```bash
git add app/services/ai/__init__.py app/services/ai/client.py
git commit -m "feat: add OpenAI-compatible AI client with stream and non-stream support"
```

---

### Task 2: Create prompt templates

**Files:** Create `app/services/ai/prompts.py`

- [ ] **Step 1: Write prompts**

```python
import json
from typing import Dict, List


def build_analysis_prompt(food_items: List[Dict], nutrition_totals: Dict, user_profile: Dict) -> str:
    return f"""你是一名注册营养师。根据以下信息分析这顿饭的营养结构，给出个性化饮食建议。

## 识别到的食物
{json.dumps(food_items, ensure_ascii=False, indent=2)}

## 营养素汇总（每100g估算）
{json.dumps(nutrition_totals, ensure_ascii=False)}

## 用户身体数据
{json.dumps(user_profile, ensure_ascii=False)}

请回复：1.**总体评价** 2.**亮点** 3.**需改善** 4.**具体建议**
用中文，300字以内，基于真实数据。"""


def build_history_recommendation_prompt(recent_records: List[Dict], user_profile: Dict) -> str:
    return f"""你是一名健康管理顾问。根据以下近期饮食记录，分析趋势并给出建议。

## 近期饮食记录
{json.dumps(recent_records, ensure_ascii=False, indent=2)}

## 用户身体数据
{json.dumps(user_profile, ensure_ascii=False)}

请回复：1.**饮食趋势** 2.**营养均衡度** 3.**长期建议**（3-4条）
用中文，400字以内，鼓励语气。"""


def build_chat_system_prompt(context_info: str = "") -> str:
    base = """你是一名专业的营养顾问，拥有丰富的营养学、食品安全和饮食搭配知识。
可以解答：食物营养、饮食搭配（增肌/减脂）、特殊饮食需求（糖尿病/高血压等）、食品安全与烹饪、运动营养。
要求：中文回复，知识准确语气亲切，涉及医疗问题提醒咨询医生，300字以内。"""
    if context_info:
        return base + f"\n\n## 当前上下文\n{context_info}\n\n在回复时参考以上上下文。"
    return base
```

- [ ] **Step 2: Commit**
```bash
git add app/services/ai/prompts.py
git commit -m "feat: add AI prompt templates for analysis, history, and chat"
```

---

### Task 3: Create SSE streaming utility

**Files:** Create `app/services/ai/streaming.py`

- [ ] **Step 1: Write streaming module**

```python
import json, asyncio
from typing import AsyncIterator, Dict, Optional
from fastapi.responses import StreamingResponse
from app.log import logger
from app.services.ai.client import ai_client
from app.services.ai.prompts import (
    build_analysis_prompt, build_chat_system_prompt, build_history_recommendation_prompt
)


async def sse_generator(user_id: int, scenario: str, **kwargs) -> AsyncIterator[str]:
    from app.models.admin import User
    from app.utils.crypto import decrypt_api_key

    user = await User.get(id=user_id)
    api_key_enc = getattr(user, "api_key", None)
    if not api_key_enc:
        yield _sse("error", "请先在个人资料中配置 AI API Key")
        return
    api_key = decrypt_api_key(api_key_enc)
    base_url = getattr(user, "ai_base_url", None)
    model = getattr(user, "ai_model", None)
    messages = _build_messages(scenario, **kwargs)

    try:
        full = ""
        async for token in ai_client.chat_stream(messages, api_key, base_url, model):
            full += token
            yield _sse("token", token)
            await asyncio.sleep(0)
        yield _sse("done", "", {"content": full})
    except Exception as exc:
        logger.error(f"SSE error: {str(exc)}")
        yield _sse("error", str(exc))


def _sse(event_type: str, data: str, extra: Optional[Dict] = None) -> str:
    payload = {"type": event_type, "content": data}
    if extra: payload.update(extra)
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _build_messages(scenario: str, **kwargs) -> list:
    if scenario == "analysis":
        system = build_analysis_prompt(
            food_items=kwargs.get("food_items", []),
            nutrition_totals=kwargs.get("nutrition_totals", {}),
            user_profile=kwargs.get("user_profile", {}))
        return [{"role": "system", "content": system},
                {"role": "user", "content": "请分析这顿饭的营养结构并给出建议。"}]
    elif scenario == "history":
        system = build_history_recommendation_prompt(
            recent_records=kwargs.get("recent_records", []),
            user_profile=kwargs.get("user_profile", {}))
        return [{"role": "system", "content": system},
                {"role": "user", "content": "请分析我的近期饮食情况，给出改善建议。"}]
    elif scenario == "chat":
        ctx = kwargs.get("context", "")
        system = build_chat_system_prompt(ctx)
        return [{"role": "system", "content": system}] + kwargs.get("messages", [])
    return [{"role": "user", "content": "你好"}]


def create_streaming_response(user_id: int, scenario: str, **kwargs) -> StreamingResponse:
    return StreamingResponse(
        sse_generator(user_id, scenario, **kwargs),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
```

- [ ] **Step 2: Commit**
```bash
git add app/services/ai/streaming.py
git commit -m "feat: add SSE streaming utility for AI responses"
```

---

### Task 4: Create AI service orchestration

**Files:** Create `app/services/ai/service.py`

- [ ] **Step 1: Write service module**

```python
from typing import Dict, List
from app.core.exceptions import CustomException
from app.log import logger
from app.models.admin import User
from app.models.food import Nutrition, NutritionRecommendation, RecognitionRecord
from app.services.ai.client import ai_client
from app.services.ai.prompts import build_analysis_prompt, build_history_recommendation_prompt, build_chat_system_prompt
from app.utils.crypto import decrypt_api_key


class AiService:

    @staticmethod
    async def _get_user_ai_config(user_id: int) -> tuple:
        user = await User.get(id=user_id)
        encrypted = getattr(user, "api_key", None)
        if not encrypted:
            raise CustomException(message="请先在个人资料中配置 AI API Key", code=400)
        return decrypt_api_key(encrypted), getattr(user, "ai_base_url", None), getattr(user, "ai_model", None)

    @staticmethod
    async def _get_user_profile(user_id: int) -> Dict:
        user = await User.get(id=user_id)
        h, w, g, a = getattr(user, "height_cm", None), getattr(user, "weight_kg", None), getattr(user, "gender", None), getattr(user, "age", None)
        bmi, status = None, "未知"
        if h and w:
            bmi = round(float(w) / ((h / 100) ** 2), 1)
            if bmi < 18.5: status = "偏瘦"
            elif 24 <= bmi < 28: status = "超重"
            elif bmi >= 28: status = "肥胖"
            else: status = "正常"
        return {"身高": f"{h}cm" if h else "未设置", "体重": f"{w}kg" if w else "未设置",
                "性别": {1: "男", 2: "女", 3: "其他"}.get(g, "未设置"),
                "年龄": f"{a}岁" if a else "未设置",
                "BMI": f"{bmi}（{status}）" if bmi else "未计算"}

    async def _build_record_context(self, record_id: int) -> tuple:
        record = await RecognitionRecord.get_or_none(id=record_id).prefetch_related(
            "analysis", "details", "details__food", "details__food__nutrition")
        if not record: raise CustomException(message="识别记录不存在", code=404)
        items = []
        totals = {"热量_kcal": 0, "蛋白质_g": 0, "脂肪_g": 0, "碳水_g": 0, "纤维_g": 0, "钠_mg": 0}
        if record.details:
            for d in record.details:
                item = {"食物": (d.food.chinese_name or d.food.name) if d.food else "未知",
                        "置信度": f"{d.confidence * 100:.1f}%"}
                if d.food:
                    n = await Nutrition.get_or_none(food=d.food)
                    if n:
                        item["营养(每100g)"] = {"热量": f"{n.energy}kcal", "蛋白质": f"{n.protein}g",
                                                 "脂肪": f"{n.fat}g", "碳水": f"{n.carbohydrate}g"}
                        for k, v in [("热量_kcal", n.energy), ("蛋白质_g", n.protein),
                                      ("脂肪_g", n.fat), ("碳水_g", n.carbohydrate)]:
                            totals[k] += float(v or 0)
                items.append(item)
        return items, totals

    async def analyze_record(self, record_id: int, user_id: int) -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        items, totals = await self._build_record_context(record_id)
        profile = await self._get_user_profile(user_id)
        system = build_analysis_prompt(items, totals, profile)
        result = await ai_client.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": "请分析这顿饭。"}],
            api_key, base_url, model)
        await NutritionRecommendation.create(
            user_id=user_id, record_id=record_id, content=result["content"],
            reference=f"AI分析 record_id={record_id} model={model}")
        return {"record_id": record_id, "content": result["content"]}

    async def generate_history_recommendation(self, user_id: int) -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        records = await RecognitionRecord.filter(user_id=user_id).order_by("-created_at").limit(10).prefetch_related("analysis")
        recent = [{"时间": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                   "热量_kcal": r.analysis.total_energy if r.analysis else 0,
                   "蛋白质_g": r.analysis.total_protein if r.analysis else 0, "状态": r.status} for r in records]
        system = build_history_recommendation_prompt(recent, await self._get_user_profile(user_id))
        result = await ai_client.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": "请分析我的饮食情况，给出改善建议。"}],
            api_key, base_url, model)
        await NutritionRecommendation.create(
            user_id=user_id, content=result["content"],
            reference=f"AI历史分析 records={len(recent)} model={model}")
        return {"content": result["content"]}

    async def chat(self, user_id: int, messages: List[Dict], context: str = "") -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        system = build_chat_system_prompt(context)
        result = await ai_client.chat([{"role": "system", "content": system}] + messages, api_key, base_url, model)
        await NutritionRecommendation.create(
            user_id=user_id, content=result["content"],
            reference=f"AI对话 messages={len(messages)} model={model}")
        return {"content": result["content"]}

    async def test_connection(self, user_id: int) -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        return await ai_client.test_connection(api_key, base_url, model)


ai_service = AiService()
```

- [ ] **Step 2: Commit**
```bash
git add app/services/ai/service.py
git commit -m "feat: add AI service orchestration for analysis, history, and chat"
```

---

### Task 5: Add AI fields to User model

**Files:** Modify `app/models/admin.py`

- [ ] **Step 1: Add after `age` field (line 26)**

```python
    api_key = fields.TextField(null=True, description="用户AI API Key（加密存储）")
    ai_model = fields.CharField(max_length=100, null=True, default="deepseek-chat", description="用户选择的AI模型")
    ai_base_url = fields.CharField(max_length=255, null=True, description="自定义AI API地址")
```

- [ ] **Step 2: Run migration and commit**
```bash
aerich migrate && aerich upgrade
git add app/models/admin.py migrations/
git commit -m "feat: add AI API key, model, and base URL fields to User model"
```

---

### Task 6: Create schemas and encryption utility

**Files:** Create `app/schemas/ai.py`, `app/utils/crypto.py`; Modify `app/schemas/users.py`

- [ ] **Step 1: Write `app/schemas/ai.py`**

```python
from typing import List, Optional
from pydantic import BaseModel, Field


class AiConfigUpdate(BaseModel):
    api_key: Optional[str] = Field(None)
    ai_model: Optional[str] = Field(None, max_length=100)
    ai_base_url: Optional[str] = Field(None, max_length=255)


class AiChatMessage(BaseModel):
    role: str
    content: str


class AiChatRequest(BaseModel):
    messages: List[AiChatMessage]
    context: Optional[str] = None
```

- [ ] **Step 2: Write `app/utils/crypto.py`**

```python
import base64, hashlib
from app.settings.config import settings

def _key_bytes() -> bytes:
    return hashlib.sha256(settings.SECRET_KEY.encode()).digest()

def encrypt_api_key(plain: str) -> str:
    key = _key_bytes()
    return base64.urlsafe_b64encode(
        bytes(p ^ key[i % len(key)] for i, p in enumerate(plain.encode("utf-8")))).decode()

def decrypt_api_key(encrypted: str) -> str:
    key = _key_bytes()
    return bytes(e ^ key[i % len(key)] for i, e in
                 enumerate(base64.urlsafe_b64decode(encrypted.encode()))).decode("utf-8")
```

- [ ] **Step 3: Modify `app/schemas/users.py`**

In `BaseUser`, after `age`:
```python
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    has_api_key: bool = False
```

In `UserSelfUpdate`, after `age`:
```python
    api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
```

- [ ] **Step 4: Commit**
```bash
git add app/schemas/ai.py app/utils/crypto.py app/schemas/users.py
git commit -m "feat: add AI config schemas and API key encryption utility"
```

---

### Task 7: Create AI API routes

**Files:** Create `app/api/v1/ai/__init__.py`, `app/api/v1/ai/ai.py`

- [ ] **Step 1: Write route handlers**

```python
from fastapi import APIRouter, Depends
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.food import Nutrition, RecognitionRecord
from app.schemas.ai import AiChatRequest
from app.schemas.base import Fail, Success
from app.services.ai.service import ai_service
from app.services.ai.streaming import create_streaming_response
from app.core.exceptions import CustomException
from app.log import logger

ai_router = APIRouter()


@ai_router.post("/analyze/record/{record_id}", summary="AI分析识别记录", dependencies=[DependAuth])
async def analyze_record(record_id: int):
    try:
        return Success(data=await ai_service.analyze_record(record_id, CTX_USER_ID.get()))
    except CustomException as e: return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        return Fail(code=500, msg=f"AI分析失败: {str(e)}")


@ai_router.post("/analyze/record/{record_id}/stream", summary="AI流式分析", dependencies=[DependAuth])
async def analyze_record_stream(record_id: int):
    user_id = CTX_USER_ID.get()
    record = await RecognitionRecord.get_or_none(id=record_id, user_id=user_id).prefetch_related(
        "analysis", "details", "details__food", "details__food__nutrition")
    if not record: raise CustomException(message="识别记录不存在", code=404)
    items, totals = await ai_service._build_record_context(record_id)
    profile = await ai_service._get_user_profile(user_id)
    return create_streaming_response(user_id=user_id, scenario="analysis",
                                     food_items=items, nutrition_totals=totals, user_profile=profile)


@ai_router.post("/analyze/history", summary="AI分析历史", dependencies=[DependAuth])
async def analyze_history():
    try:
        return Success(data=await ai_service.generate_history_recommendation(CTX_USER_ID.get()))
    except CustomException as e: return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI history failed: {str(e)}")
        return Fail(code=500, msg=f"AI历史分析失败: {str(e)}")


@ai_router.post("/analyze/history/stream", summary="AI流式分析历史", dependencies=[DependAuth])
async def analyze_history_stream():
    user_id = CTX_USER_ID.get()
    records = await RecognitionRecord.filter(user_id=user_id).order_by("-created_at").limit(10).prefetch_related("analysis")
    recent = [{"时间": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
               "热量_kcal": r.analysis.total_energy if r.analysis else 0,
               "蛋白质_g": r.analysis.total_protein if r.analysis else 0, "状态": r.status} for r in records]
    return create_streaming_response(user_id=user_id, scenario="history",
                                     recent_records=recent, user_profile=await ai_service._get_user_profile(user_id))


@ai_router.post("/chat", summary="AI营养对话", dependencies=[DependAuth])
async def ai_chat(req: AiChatRequest):
    try:
        msgs = [{"role": m.role, "content": m.content} for m in req.messages]
        return Success(data=await ai_service.chat(CTX_USER_ID.get(), msgs, req.context or ""))
    except CustomException as e: return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI chat failed: {str(e)}")
        return Fail(code=500, msg=f"AI对话失败: {str(e)}")


@ai_router.post("/chat/stream", summary="AI流式对话", dependencies=[DependAuth])
async def ai_chat_stream(req: AiChatRequest):
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    return create_streaming_response(user_id=CTX_USER_ID.get(), scenario="chat",
                                     messages=msgs, context=req.context or "")


@ai_router.post("/test", summary="测试AI连接", dependencies=[DependAuth])
async def test_ai():
    try:
        return Success(data=await ai_service.test_connection(CTX_USER_ID.get()), msg="连接成功")
    except CustomException as e: return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI test failed: {str(e)}")
        return Fail(code=500, msg=f"连接测试失败: {str(e)}")
```

- [ ] **Step 2: Commit**
```bash
git add app/api/v1/ai/
git commit -m "feat: add AI API routes for analysis, chat, and test"
```

---

### Task 8: Register routes and add config to base

**Files:** Modify `app/api/v1/__init__.py`, `app/api/v1/base/base.py`, `app/settings/config.py`

- [ ] **Step 1: Register AI router in `app/api/v1/__init__.py`**

Add import: `from .ai import ai_router`
Add: `v1_router.include_router(ai_router, prefix="/ai")`

- [ ] **Step 2: Add AI config endpoints in `app/api/v1/base/base.py`**

Add imports:
```python
from app.schemas.ai import AiConfigUpdate
from app.utils.crypto import encrypt_api_key, decrypt_api_key
```

Add routes:
```python
@router.get("/profile/ai-config", summary="获取用户AI配置", dependencies=[DependAuth])
async def get_ai_config():
    user_id = CTX_USER_ID.get()
    user = await User.get(id=user_id)
    key = getattr(user, "api_key", None) or ""
    masked = ""
    if key:
        d = decrypt_api_key(key)
        masked = d[:4] + "****" + d[-4:] if len(d) > 8 else "****"
    return Success(data={"api_key": masked, "ai_model": getattr(user, "ai_model", None) or "deepseek-chat",
                         "ai_base_url": getattr(user, "ai_base_url", None) or "", "has_configured": bool(key)})

@router.put("/profile/ai-config", summary="更新用户AI配置", dependencies=[DependAuth])
async def update_ai_config(req: AiConfigUpdate):
    user_id = CTX_USER_ID.get()
    user = await User.get(id=user_id)
    if req.api_key is not None: user.api_key = encrypt_api_key(req.api_key) if req.api_key else None
    if req.ai_model is not None: user.ai_model = req.ai_model
    if req.ai_base_url is not None: user.ai_base_url = req.ai_base_url
    await user.save()
    key = getattr(user, "api_key", None) or ""
    masked = ""
    if key:
        d = decrypt_api_key(key)
        masked = d[:4] + "****" + d[-4:] if len(d) > 8 else "****"
    return Success(data={"api_key": masked, "ai_model": user.ai_model or "deepseek-chat",
                         "ai_base_url": user.ai_base_url or "", "has_configured": bool(key)}, msg="AI配置更新成功")
```

In `get_userinfo`, add after avatar line:
```python
data["has_api_key"] = bool(getattr(user_obj, "api_key", None))
```

- [ ] **Step 3: Add to `app/settings/config.py`**

```python
AI_DEFAULT_MODEL: str = "deepseek-chat"
AI_DEFAULT_BASE_URL: str = "https://api.deepseek.com"
```

- [ ] **Step 4: Commit**
```bash
git add app/api/v1/__init__.py app/api/v1/base/base.py app/settings/config.py
git commit -m "feat: register AI router and add user AI config endpoints"
```

---

### Task 9: Frontend — API calls

**Files:** Modify `web/src/api/index.js`

- [ ] **Step 1: Add to exported object**

```javascript
  // ai config
  getAiConfig: () => request.get('/base/profile/ai-config'),
  updateAiConfig: (data = {}) => request.put('/base/profile/ai-config', data),
  // ai analysis
  aiAnalyzeRecord: (id) => request.post(`/ai/analyze/record/${id}`),
  aiAnalyzeRecordStreamUrl: (id) =>
    `${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/ai/analyze/record/${id}/stream`,
  aiAnalyzeHistory: () => request.post('/ai/analyze/history'),
  // ai chat
  aiChat: (data = {}) => request.post('/ai/chat', data),
  aiChatStreamUrl: () => `${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/ai/chat/stream`,
  // ai test
  aiTestConnection: () => request.post('/ai/test'),
```

- [ ] **Step 2: Commit**
```bash
git add web/src/api/index.js
git commit -m "feat: add AI API calls to frontend"
```

---

### Task 10: Frontend — AiStreamRenderer component

**Files:** Create `web/src/components/ai/AiStreamRenderer.vue`

- [ ] **Step 1: Install markdown-it**
```bash
cd web && pnpm add markdown-it
```

- [ ] **Step 2: Write component**

```vue
<template><div class="ai-stream" v-html="rendered"></div></template>
<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
const props = defineProps({ content: { type: String, default: '' } })
const md = new MarkdownIt({ breaks: true, linkify: true })
const rendered = computed(() => md.render(props.content || '...'))
</script>
<style scoped>
.ai-stream { line-height:1.8; color:#334155 }
.ai-stream :deep(h1),.ai-stream :deep(h2),.ai-stream :deep(h3) { margin:12px 0 6px; font-weight:600 }
.ai-stream :deep(ul),.ai-stream :deep(ol) { padding-left:20px }
.ai-stream :deep(li) { margin:4px 0 }
.ai-stream :deep(strong) { color:#1e293b }
</style>
```

- [ ] **Step 3: Commit**
```bash
git add web/src/components/ai/AiStreamRenderer.vue web/package.json web/pnpm-lock.yaml
git commit -m "feat: add AiStreamRenderer with Markdown rendering"
```

---

### Task 11: Frontend — AiConfigForm component

**Files:** Create `web/src/components/ai/AiConfigForm.vue`

- [ ] **Step 1: Write component**

```vue
<template>
  <n-card title="AI 配置" size="small">
    <n-form label-placement="left" label-width="100">
      <n-form-item label="API Key">
        <n-input v-model:value="form.api_key" type="password" show-password-on="mousedown" placeholder="输入 API Key" />
      </n-form-item>
      <n-form-item label="模型名称">
        <n-input v-model:value="form.ai_model" placeholder="deepseek-chat, gpt-4o 等" />
      </n-form-item>
      <n-form-item label="API 地址">
        <n-input v-model:value="form.ai_base_url" placeholder="https://api.deepseek.com" />
      </n-form-item>
      <n-space>
        <n-button type="primary" :loading="saving" @click="save">保存</n-button>
        <n-button :loading="testing" @click="test">测试连接</n-button>
      </n-space>
      <div v-if="result" class="mt-3">
        <n-alert :type="result.ok ? 'success' : 'error'">{{ result.msg }}</n-alert>
      </div>
    </n-form>
  </n-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton, NSpace, NAlert, useMessage } from 'naive-ui'
import api from '@/api'

const msg = useMessage()
const saving = ref(false); const testing = ref(false); const result = ref(null)
const form = ref({ api_key: '', ai_model: 'deepseek-chat', ai_base_url: 'https://api.deepseek.com' })

onMounted(async () => {
  try {
    const r = await api.getAiConfig()
    if (r.code === 200) {
      form.value.ai_model = r.data.ai_model || 'deepseek-chat'
      form.value.ai_base_url = r.data.ai_base_url || 'https://api.deepseek.com'
    }
  } catch {}
})

async function save() {
  saving.value = true
  try {
    const p = { ai_model: form.value.ai_model, ai_base_url: form.value.ai_base_url }
    if (form.value.api_key) p.api_key = form.value.api_key
    if ((await api.updateAiConfig(p)).code === 200) { msg.success('已保存'); form.value.api_key = '' }
  } catch { msg.error('保存失败') }
  finally { saving.value = false }
}

async function test() {
  testing.value = true; result.value = null
  if (form.value.api_key) await save()
  try {
    const r = await api.aiTestConnection()
    result.value = r.code === 200 ? { ok: true, msg: `连接成功 — ${r.data.model}` } : { ok: false, msg: r.msg }
  } catch { result.value = { ok: false, msg: '连接失败' } }
  finally { testing.value = false }
}
</script>
```

- [ ] **Step 2: Commit**
```bash
git add web/src/components/ai/AiConfigForm.vue
git commit -m "feat: add AI config form component"
```

---

### Task 12: Frontend — AiChatPanel component

**Files:** Create `web/src/components/ai/AiChatPanel.vue`

- [ ] **Step 1: Write component**

```vue
<template>
  <div class="chat-panel">
    <div class="chat-msgs" ref="mc">
      <n-empty v-if="!msgs.length && !streaming" description="向 AI 营养顾问提问吧" class="chat-empty" />
      <div v-for="(m,i) in msgs" :key="i" class="chat-msg" :class="m.role">
        <n-avatar v-if="m.role==='assistant'" :size="32" src="/logo.png" />
        <n-avatar v-else :size="32">U</n-avatar>
        <div class="msg-body">
          <div class="msg-role">{{ m.role==='assistant'?'AI 顾问':'我' }}</div>
          <AiStreamRenderer v-if="m.role==='assistant'" :content="m.content" />
          <div v-else class="msg-text">{{ m.content }}</div>
        </div>
      </div>
      <div v-if="streaming" class="chat-msg assistant">
        <n-avatar :size="32" src="/logo.png" />
        <div class="msg-body"><div class="msg-role">AI 顾问</div><AiStreamRenderer :content="sc" /></div>
      </div>
    </div>
    <div class="chat-input">
      <n-input v-model:value="input" type="textarea" :autosize="{minRows:1,maxRows:4}"
        placeholder="输入营养问题..." :disabled="streaming" @keydown.enter.exact.prevent="send" />
      <n-button type="primary" :disabled="!input.trim()||streaming" :loading="streaming" @click="send">
        <TheIcon icon="mdi:send" :size="18" />
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { NEmpty, NAvatar, NInput, NButton, useMessage } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import AiStreamRenderer from './AiStreamRenderer.vue'
import api from '@/api'

const props = defineProps({ context: { type: String, default: '' } })
const msgRef = useMessage()
const msgs = ref([])
const input = ref('')
const streaming = ref(false)
const sc = ref('')
const mc = ref(null)

async function send() {
  const t = input.value.trim()
  if (!t || streaming.value) return
  msgs.value.push({ role: 'user', content: t }); input.value = ''
  streaming.value = true; sc.value = ''; await nextTick(); scroll()

  try {
    const tok = localStorage.getItem('token') || ''
    const r = await fetch(api.aiChatStreamUrl(), {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'token': tok },
      body: JSON.stringify({ messages: msgs.value.map(m=>({role:m.role,content:m.content})), context: props.context })
    })
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n'); buf = lines.pop() || ''
      for (const ln of lines) {
        if (ln.startsWith('data: ')) {
          try {
            const d = JSON.parse(ln.slice(6))
            if (d.type === 'token') sc.value += d.content
            else if (d.type === 'done') { msgs.value.push({ role: 'assistant', content: d.content || sc.value }); sc.value = '' }
            else if (d.type === 'error') msgRef.error(d.content)
          } catch {}
        }
      }
    }
  } catch { msgRef.error('连接失败') }
  finally { streaming.value = false; sc.value = ''; await nextTick(); scroll() }
}

function scroll() { if (mc.value) mc.value.scrollTop = mc.value.scrollHeight }
function clearMessages() { msgs.value = [] }
defineExpose({ clearMessages })
</script>

<style scoped>
.chat-panel { display:flex; flex-direction:column; height:100% }
.chat-msgs { flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:16px }
.chat-empty { margin:auto }
.chat-msg { display:flex; gap:12px; max-width:85% }
.chat-msg.user { align-self:flex-end; flex-direction:row-reverse }
.chat-msg.assistant { align-self:flex-start }
.msg-body { background:#f8fafc; border-radius:12px; padding:12px 16px; min-width:0 }
.chat-msg.user .msg-body { background:#dbeafe }
.msg-role { font-size:12px; color:#64748b; margin-bottom:4px; font-weight:600 }
.msg-text { color:#334155; line-height:1.7; white-space:pre-wrap }
.chat-input { display:flex; gap:8px; padding:12px 16px; border-top:1px solid #e2e8f0; background:#fff }
</style>
```

- [ ] **Step 2: Commit**
```bash
git add web/src/components/ai/AiChatPanel.vue
git commit -m "feat: add AI chat panel with streaming support"
```

---

### Task 13: Frontend — AI Advisor page

**Files:** Create `web/src/views/food/ai-advisor/index.vue`

- [ ] **Step 1: Write page**

```vue
<template>
  <div class="advisor-page">
    <n-layout has-sider class="layout">
      <n-layout-content class="chat-area"><AiChatPanel ref="cr" :context="ctx" /></n-layout-content>
      <n-layout-sider width="260" bordered class="sidebar">
        <h4>上下文</h4>
        <n-empty v-if="!ctx" description="未关联记录" size="small" />
        <n-tag v-else type="info">{{ ctx }}</n-tag>
        <n-divider />
        <n-button size="small" ghost block @click="cr?.clearMessages()">清空对话</n-button>
      </n-layout-sider>
    </n-layout>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NLayout, NLayoutContent, NLayoutSider, NDivider, NButton, NTag, NEmpty } from 'naive-ui'
import AiChatPanel from '@/components/ai/AiChatPanel.vue'
const cr = ref(null); const ctx = ref('')
</script>

<style scoped>
.advisor-page,.layout { height:100% }
.chat-area { height:100%; display:flex; flex-direction:column }
.sidebar { padding:16px }
.sidebar h4 { margin:0 0 12px; font-size:15px; color:#334155 }
</style>
```

- [ ] **Step 2: Commit**
```bash
git add web/src/views/food/ai-advisor/index.vue
git commit -m "feat: add AI nutrition advisor page"
```

---

### Task 14: Frontend — Modify profile, history, recognition pages

**Files:** Modify `web/src/views/profile/index.vue`, `web/src/views/food/history/index.vue`, `web/src/views/food/recognition/index.vue`

- [ ] **Step 1: Add AI config tab to profile**

In `profile/index.vue`, add import: `import AiConfigForm from '@/components/ai/AiConfigForm.vue'`

Add new tab pane inside `<NTabs>`:
```html
<NTabPane name="ai" tab="AI 配置">
  <div class="m-30" style="max-width:500px"><AiConfigForm /></div>
</NTabPane>
```

- [ ] **Step 2: Streaming AI in history detail**

In `history/index.vue`, add import: `import AiStreamRenderer from '@/components/ai/AiStreamRenderer.vue'`

Add: `const aiContent = ref('')`

Replace the recommendation generation part of `viewDetail` with streaming fetch to `api.aiAnalyzeRecordStreamUrl(row.id)`, reading SSE tokens into `aiContent`.

Replace the "营养建议" template section with:
```html
<n-divider dashed>AI 营养建议</n-divider>
<div v-if="recommendationLoading && !aiContent" class="recommend-loading">
  <n-spin size="small" /><span>AI 正在生成建议...</span>
</div>
<AiStreamRenderer v-else-if="aiContent" :content="aiContent" />
<n-empty v-else description="暂无营养建议" />
```

- [ ] **Step 3: AI analysis in recognition page**

In `recognition/index.vue`, add `AiStreamRenderer` import and streaming logic. After successful recognition, call `api.aiAnalyzeRecordStreamUrl(recordId)` with SSE fetch, accumulating tokens in an `aiAnalysis` ref. Add a card section below results:

```html
<n-card v-if="aiAnalysis || aiAnalysisLoading" title="AI 智能分析" class="mt-4">
  <n-spin v-if="aiAnalysisLoading && !aiAnalysis" />
  <AiStreamRenderer v-if="aiAnalysis" :content="aiAnalysis" />
</n-card>
```

- [ ] **Step 4: Commit**
```bash
git add web/src/views/profile/index.vue web/src/views/food/history/index.vue web/src/views/food/recognition/index.vue
git commit -m "feat: integrate AI into profile, history detail, and recognition pages"
```

---

### Task 15: Add route and menu for AI advisor

**Files:** Modify `web/src/router/routes/index.js` (or equivalent), `app/core/init_app.py`

- [ ] **Step 1: Add route**

```javascript
{ path: '/food/ai-advisor', name: 'AiAdvisor',
  component: () => import('@/views/food/ai-advisor/index.vue'),
  meta: { title: 'AI 营养顾问', icon: 'carbon:chat-bot' } }
```

- [ ] **Step 2: Seed menu in init_app.py**

In `init_food_data` or a new helper, add:
```python
from app.models.admin import Menu
from app.schemas.menus import MenuType

if not await Menu.filter(path="/food/ai-advisor").exists():
    await Menu.create(menu_type=MenuType.MENU, name="AI营养顾问",
        path="/food/ai-advisor", order=7, parent_id=0, icon="carbon:chat-bot",
        is_hidden=False, component="/food/ai-advisor", keepalive=False)
```

- [ ] **Step 3: Commit**
```bash
git add web/src/router/ app/core/init_app.py
git commit -m "feat: add AI advisor route and menu entry"
```

---

### Task 16: Create branch and verify

- [ ] **Step 1: Create branch**
```bash
git checkout -b ai-nutrition-analysis food_recognition
```

- [ ] **Step 2: Run backend**
```bash
python run.py
# Check: http://localhost:9999/docs for /api/v1/ai/* endpoints
```

- [ ] **Step 3: Run frontend**
```bash
cd web && pnpm dev
# Check: http://localhost:3100 for AI advisor page, profile AI config, etc.
```

- [ ] **Step 4: Test flows**
1. Profile → AI Config → Save key → Test connection
2. Food Recognition → Upload → AI analysis streams
3. History → Detail → AI streaming
4. AI Advisor → Chat → Stream response
5. No key → Error shown

- [ ] **Step 5: Fix issues, then commit final fixes**
```bash
git add -A && git commit -m "chore: final integration fixes"
```
