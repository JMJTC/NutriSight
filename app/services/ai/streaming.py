import json
import asyncio
from typing import AsyncIterator, Dict, Optional
from fastapi.responses import StreamingResponse
from app.log import logger
from app.services.ai.client import ai_client
from app.services.ai.prompts import (
    build_analysis_prompt, build_chat_system_prompt, build_history_recommendation_prompt
)


async def sse_generator(user_id: int, scenario: str, **kwargs) -> AsyncIterator[str]:
    from app.models.admin import User
    from app.models.food import NutritionRecommendation
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
    record_id = kwargs.get("record_id")

    try:
        full = ""
        async for token in ai_client.chat_stream(messages, api_key, base_url, model):
            full += token
            yield _sse("token", token)
            await asyncio.sleep(0)

        # Persist result
        saved_id = None
        if record_id:
            try:
                rec = await NutritionRecommendation.create(
                    user=user,
                    record_id=record_id,
                    content=full,
                    reference=f"AI分析 record_id={record_id} model={model}",
                )
                saved_id = rec.id
            except Exception as e:
                logger.error(f"Failed to save AI recommendation: {str(e)}")

        yield _sse("done", "", {"content": full, "record_id": saved_id})
    except Exception as exc:
        logger.error(f"SSE error: {str(exc)}")
        yield _sse("error", str(exc))


def _sse(event_type: str, data: str, extra: Optional[Dict] = None) -> str:
    payload = {"type": event_type, "content": data}
    if extra:
        payload.update(extra)
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
