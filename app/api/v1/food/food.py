from fastapi import APIRouter, UploadFile, File, Request, Depends, Query
from app.controllers.food import FoodController
from app.schemas.food import RecognitionResponse
from app.core.ctx import CTX_USER_ID

food_router = APIRouter()

@food_router.post("/recognize", response_model=RecognitionResponse, summary="上传图片并识别食物")
async def recognize_food(
    file: UploadFile = File(...),
):
    user_id = CTX_USER_ID.get()
    # Mock user_id if context is missing during dev/test without auth
    if not user_id:
        user_id = 1 # Fallback or handle error
        
    return await FoodController.recognize_food(file, user_id)

@food_router.get("/history", summary="获取识别历史")
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    user_id = CTX_USER_ID.get() or 1
    return await FoodController.get_history(user_id, page, page_size)

@food_router.get("/record/{record_id}", summary="获取识别记录详情")
async def get_record_detail(record_id: int):
    user_id = CTX_USER_ID.get() or 1
    return await FoodController.get_record_detail(record_id, user_id)
