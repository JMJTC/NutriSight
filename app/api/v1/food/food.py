import logging
from typing import Optional

from fastapi import APIRouter, Query, UploadFile, File, Depends

from app.controllers.food import FoodController
from app.core.dependency import DependAuth
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.food import (
    FoodCategoryCreate,
    FoodCategoryUpdate,
    NutritionCreate,
)
from app.core.exceptions import CustomException

logger = logging.getLogger(__name__)

food_router = APIRouter()


@food_router.post("/recognize", summary="上传图片进行食物识别")
async def recognize_food(
    file: UploadFile = File(..., description="食物图片"),
    current_user = DependAuth,
):
    """
    上传食物图片进行识别
    
    - 支持 jpg, png, bmp, webp 等常见图片格式
    - 返回识别结果和营养分析
    """
    try:
        # 从认证用户获取 user_id
        user_id = current_user.id
        result = await FoodController.recognize_food(file, user_id)
        return Success(data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Recognition failed: {str(e)}")
        return Fail(code=500, msg=f"识别失败: {str(e)}")


@food_router.get("/history", summary="获取用户的食物识别历史")
async def get_recognition_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user = DependAuth,
):
    """
    获取当前用户的食物识别历史记录
    """
    try:
        user_id = current_user.id
        data = await FoodController.get_history(user_id, page, page_size)
        return SuccessExtra(
            data=data["items"],
            total=data["total"],
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Failed to fetch history: {str(e)}")
        return Fail(code=500, msg=f"获取历史记录失败: {str(e)}")


@food_router.get("/record/{record_id}", summary="获取识别记录的详细信息")
async def get_record_detail(
    record_id: int,
    current_user = DependAuth,
):
    """
    获取单条识别记录的详细信息，包括识别的食物、营养信息等
    """
    try:
        user_id = current_user.id
        result = await FoodController.get_record_detail(record_id, user_id)
        return Success(data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to fetch record detail: {str(e)}")
        return Fail(code=500, msg=f"获取记录详情失败: {str(e)}")


@food_router.get("/categories", summary="获取所有食物类别")
async def get_food_categories(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
    search: Optional[str] = Query(None, description="食物名称搜索"),
):
    """
    获取系统中所有的食物类别信息
    """
    try:
        data = await FoodController.get_food_categories(page, page_size, search)
        return SuccessExtra(
            data=data["items"],
            total=data["total"],
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Failed to fetch categories: {str(e)}")
        return Fail(code=500, msg=f"获取食物类别失败: {str(e)}")


@food_router.post("/categories", summary="创建食物类别")
async def create_food_category(
    category_in: FoodCategoryCreate,
):
    """
    创建新的食物类别
    """
    try:
        result = await FoodController.create_food_category(category_in)
        return Success(msg="食物类别创建成功", data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to create category: {str(e)}")
        return Fail(code=500, msg=f"创建食物类别失败: {str(e)}")


@food_router.put("/categories/{category_id}", summary="更新食物类别")
async def update_food_category(
    category_id: int,
    category_in: FoodCategoryUpdate,
):
    """
    更新食物类别信息
    """
    try:
        result = await FoodController.update_food_category(category_id, category_in)
        return Success(msg="食物类别更新成功", data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to update category: {str(e)}")
        return Fail(code=500, msg=f"更新食物类别失败: {str(e)}")


@food_router.post("/nutrition", summary="添加/更新营养信息")
async def add_nutrition_info(
    nutrition_in: NutritionCreate,
):
    """
    为食物类别添加或更新营养成分信息
    """
    try:
        result = await FoodController.add_nutrition_info(nutrition_in)
        return Success(msg="营养信息保存成功", data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to save nutrition info: {str(e)}")
        return Fail(code=500, msg=f"保存营养信息失败: {str(e)}")


@food_router.get("/status", summary="获取服务状态 [调试]")
async def get_service_status():
    """
    获取 YOLO 服务和数据库状态（用于调试）
    """
    try:
        status = await FoodController.get_service_status()
        return Success(data=status)
    except Exception as e:
        logger.error(f"Failed to get service status: {str(e)}")
        return Fail(code=500, msg=f"获取服务状态失败: {str(e)}")
