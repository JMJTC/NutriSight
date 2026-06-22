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

ai_router = APIRouter(tags=["AI服务"])


@ai_router.post("/analyze/record/{record_id}", summary="AI分析识别记录", dependencies=[DependAuth])
async def analyze_record(record_id: int):
    try:
        return Success(data=await ai_service.analyze_record(record_id, CTX_USER_ID.get()))
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        return Fail(code=500, msg=f"AI分析失败: {str(e)}")


@ai_router.post("/analyze/record/{record_id}/stream", summary="AI流式分析", dependencies=[DependAuth])
async def analyze_record_stream(record_id: int):
    user_id = CTX_USER_ID.get()
    # Verify record exists and belongs to user
    record = await RecognitionRecord.get_or_none(id=record_id, user_id=user_id).prefetch_related(
        "analysis", "details", "details__food", "details__food__nutrition")
    if not record:
        raise CustomException(message="识别记录不存在", code=404)

    items, totals = await ai_service._build_record_context(record_id)
    profile = await ai_service._get_user_profile(user_id)
    return create_streaming_response(
        user_id=user_id, scenario="analysis", record_id=record_id,
        food_items=items, nutrition_totals=totals, user_profile=profile)


@ai_router.get("/recommendation/{record_id}", summary="获取记录的AI建议缓存", dependencies=[DependAuth])
async def get_record_recommendation(record_id: int):
    from app.models.food import NutritionRecommendation

    user_id = CTX_USER_ID.get()
    rec = await NutritionRecommendation.filter(
        user_id=user_id, record_id=record_id
    ).order_by("-created_at").first()
    if not rec:
        return Fail(code=404, msg="暂无AI建议")
    return Success(data={"content": rec.content, "created_at": rec.created_at.isoformat()})


@ai_router.post("/analyze/history", summary="AI分析历史", dependencies=[DependAuth])
async def analyze_history():
    try:
        return Success(data=await ai_service.generate_history_recommendation(CTX_USER_ID.get()))
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI history failed: {str(e)}")
        return Fail(code=500, msg=f"AI历史分析失败: {str(e)}")


@ai_router.post("/analyze/history/stream", summary="AI流式分析历史", dependencies=[DependAuth])
async def analyze_history_stream():
    user_id = CTX_USER_ID.get()
    records = await RecognitionRecord.filter(user_id=user_id).order_by("-created_at").limit(10).prefetch_related("analysis")
    recent = []
    for r in records:
        recent.append({
            "时间": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
            "热量_kcal": r.analysis.total_energy if r.analysis else 0,
            "蛋白质_g": r.analysis.total_protein if r.analysis else 0,
            "状态": r.status,
        })
    return create_streaming_response(
        user_id=user_id, scenario="history",
        recent_records=recent, user_profile=await ai_service._get_user_profile(user_id))


@ai_router.post("/chat", summary="AI营养对话", dependencies=[DependAuth])
async def ai_chat(req: AiChatRequest):
    try:
        msgs = [{"role": m.role, "content": m.content} for m in req.messages]
        return Success(data=await ai_service.chat(CTX_USER_ID.get(), msgs, req.context or ""))
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI chat failed: {str(e)}")
        return Fail(code=500, msg=f"AI对话失败: {str(e)}")


@ai_router.post("/chat/stream", summary="AI流式对话", dependencies=[DependAuth])
async def ai_chat_stream(req: AiChatRequest):
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    return create_streaming_response(
        user_id=CTX_USER_ID.get(), scenario="chat",
        messages=msgs, context=req.context or "")


@ai_router.post("/test", summary="测试AI连接", dependencies=[DependAuth])
async def test_ai():
    try:
        return Success(data=await ai_service.test_connection(CTX_USER_ID.get()), msg="连接成功")
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"AI test failed: {str(e)}")
        return Fail(code=500, msg=f"连接测试失败: {str(e)}")
