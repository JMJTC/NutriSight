from typing import Optional, List
import json

from fastapi import APIRouter, Query, UploadFile, File, Depends, Form, Body

from app.controllers.food import FoodController
from app.core.dependency import DependAuth
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.food import (
    FoodCategoryCreate,
    FoodCategoryUpdate,
    NutritionCreate,
    RecommendationRequest,
)
from app.core.exceptions import CustomException
from app.log import logger

food_router = APIRouter()


@food_router.post("/recommendation", summary="获取营养推荐", dependencies=[DependAuth])
async def get_recommendation(req: RecommendationRequest):
    """根据身体数据生成推荐建议"""
    user_id = CTX_USER_ID.get()
    
    # 按照需求返回 422 错误信息
    if req.height_cm is None or req.weight_kg is None or req.gender is None or req.age is None:
        raise CustomException(message="缺少基础身体数据，无法生成营养建议", code=422)
        
    res = await FoodController.get_nutrition_recommendation(
        user_id=user_id,
        height=req.height_cm,
        weight=req.weight_kg,
        gender=req.gender,
        age=req.age
    )
    return Success(data=res)


@food_router.post("/recognize", summary="上传图片进行食物识别", dependencies=[DependAuth])
async def recognize_food(
    file: UploadFile = File(..., description="食物图片"),
):
    """
    上传食物图片进行识别
    
    - 支持 jpg, png, bmp, webp 等常见图片格式
    - 返回识别结果和营养分析
    """
    try:
        # 从上下文获取认证用户的id
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(code=401, msg="未授权")
        result = await FoodController.recognize_food(file, user_id)
        return Success(data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Recognition failed: {str(e)}")
        return Fail(code=500, msg=f"识别失败: {str(e)}")


@food_router.get("/history", summary="获取用户的食物识别历史", dependencies=[DependAuth])
async def get_recognition_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
):
    """
    获取当前用户的食物识别历史记录
    """
    try:
        user_id = CTX_USER_ID.get()
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


@food_router.get("/record/{record_id}", summary="获取识别记录的详细信息", dependencies=[DependAuth])
async def get_record_detail(
    record_id: int,
):
    """
    获取单条识别记录的详细信息，包括识别的食物、营养信息等
    """
    try:
        user_id = CTX_USER_ID.get()
        result = await FoodController.get_record_detail(record_id, user_id)
        return Success(data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to fetch record detail: {str(e)}")
        return Fail(code=500, msg=f"获取记录详情失败: {str(e)}")


@food_router.post("/record/{record_id}/recommendation", summary="生成并保存该记录的饮食建议", dependencies=[DependAuth])
async def generate_record_recommendation(
    record_id: int,
):
    try:
        user_id = CTX_USER_ID.get()
        result = await FoodController.generate_record_recommendation(record_id, user_id)
        return Success(data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to generate record recommendation: {str(e)}")
        return Fail(code=500, msg=f"生成饮食建议失败: {str(e)}")


@food_router.delete("/record/{record_id}", summary="删除识别记录", dependencies=[DependAuth])
async def delete_record(
    record_id: int,
):
    """
    删除指定的识别记录及其关联文件
    """
    try:
        user_id = CTX_USER_ID.get()
        await FoodController.delete_record(record_id, user_id)
        return Success(msg="记录删除成功")
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to delete record: {str(e)}")
        return Fail(code=500, msg=f"删除记录失败: {str(e)}")


@food_router.delete("/records/batch", summary="批量删除识别记录", dependencies=[DependAuth])
async def delete_records_batch(
    record_ids: List[int] = Body(..., embed=True, description="要删除的记录ID列表"),
):
    """
    批量删除识别记录及其关联文件
    """
    try:
        user_id = CTX_USER_ID.get()
        count = await FoodController.delete_records(record_ids, user_id)
        return Success(msg=f"成功删除 {count} 条记录")
    except Exception as e:
        logger.error(f"Failed to delete records in batch: {str(e)}")
        return Fail(code=500, msg=f"批量删除失败: {str(e)}")


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


# =========== 食物类别管理 CRUD 端点 ===========

@food_router.get("/categories/{category_id}", summary="获取单个食物类别详情")
async def get_food_category_detail(
    category_id: int,
):
    """
    获取单个食物类别的详细信息，包括营养信息
    """
    try:
        result = await FoodController.get_food_category_detail(category_id)
        return Success(data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to get category detail: {str(e)}")
        return Fail(code=500, msg=f"获取食物类别详情失败: {str(e)}")


@food_router.delete("/categories/{category_id}", summary="删除食物类别")
async def delete_food_category(
    category_id: int,
):
    """
    删除食物类别及其关联的营养信息
    """
    try:
        await FoodController.delete_food_category(category_id)
        return Success(msg="食物类别删除成功")
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to delete category: {str(e)}")
        return Fail(code=500, msg=f"删除食物类别失败: {str(e)}")


@food_router.post("/categories/upload", summary="创建食物类别（支持图片上传）")
async def create_food_category_with_upload(
    name: str = Form(..., description="食物名称"),
    code: Optional[str] = Form(None, description="YOLO 类别 ID（可选，自动生成）"),
    food_type: Optional[str] = Form(None, description="食物类型"),
    description: Optional[str] = Form(None, description="食物描述"),
    image: Optional[UploadFile] = File(None, description="食物图片"),
    nutrition: Optional[str] = Form(None, description="营养信息 JSON"),
):
    """
    创建新的食物类别，支持在创建时直接上传图片和营养信息
    
    - code 为可选项，如不提供会自动生成
    - nutrition 参数应为 JSON 字符串，格式如下：
    {
        "energy": 52.0,
        "protein": 0.26,
        "fat": 0.17,
        "carbohydrate": 13.81,
        "fiber": 2.4,
        "sodium": 2.0
    }
    """
    try:
        # 将code字符串转换为整数（如果提供的话）
        int_code = None
        if code and code != "":
            try:
                int_code = int(code)
            except ValueError:
                return Fail(code=400, msg="YOLO 类别 ID 必须是整数")
        
        nutrition_data = None
        if nutrition:
            try:
                nutrition_data = json.loads(nutrition)
            except json.JSONDecodeError:
                return Fail(code=400, msg="营养信息 JSON 格式错误")
        
        result = await FoodController.create_food_category_with_file(
            name=name,
            code=int_code,
            food_type=food_type,
            description=description,
            image_file=image,
            nutrition_data=nutrition_data
        )
        return Success(msg="食物类别创建成功", data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to create category with upload: {str(e)}")
        return Fail(code=500, msg=f"创建食物类别失败: {str(e)}")


@food_router.put("/categories/{category_id}/upload", summary="更新食物类别（支持图片上传）")
async def update_food_category_with_upload(
    category_id: int,
    name: Optional[str] = Form(None, description="食物名称"),
    food_type: Optional[str] = Form(None, description="食物类型"),
    description: Optional[str] = Form(None, description="食物描述"),
    image: Optional[UploadFile] = File(None, description="新的食物图片"),
    image_url: Optional[str] = Form(None, description="图片 URL（当不上传图片时使用）"),
    nutrition: Optional[str] = Form(None, description="营养信息 JSON"),
):
    """
    更新食物类别信息，支持上传新的图片和更新营养信息
    """
    try:
        nutrition_data = None
        if nutrition:
            try:
                nutrition_data = json.loads(nutrition)
            except json.JSONDecodeError:
                return Fail(code=400, msg="营养信息 JSON 格式错误")
        
        result = await FoodController.update_food_category_with_file(
            category_id=category_id,
            name=name,
            food_type=food_type,
            description=description,
            image_file=image,
            image_url=image_url,
            nutrition_data=nutrition_data
        )
        return Success(msg="食物类别更新成功", data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to update category with upload: {str(e)}")
        return Fail(code=500, msg=f"更新食物类别失败: {str(e)}")


@food_router.put("/nutrition/{food_id}", summary="更新食物的营养信息")
async def update_nutrition_info(
    food_id: int,
    energy: float = Form(..., ge=0, description="热量 (kcal/100g)"),
    protein: float = Form(..., ge=0, description="蛋白质 (g/100g)"),
    fat: float = Form(..., ge=0, description="脂肪 (g/100g)"),
    carbohydrate: float = Form(..., ge=0, description="碳水化合物 (g/100g)"),
    fiber: float = Form(0.0, ge=0, description="膳食纤维 (g/100g)"),
    sodium: float = Form(0.0, ge=0, description="钠 (mg/100g)"),
):
    """
    更新食物的营养信息
    """
    try:
        nutrition_data = {
            "energy": energy,
            "protein": protein,
            "fat": fat,
            "carbohydrate": carbohydrate,
            "fiber": fiber,
            "sodium": sodium
        }
        result = await FoodController.update_food_category_with_file(
            category_id=food_id,
            nutrition_data=nutrition_data
        )
        return Success(msg="营养信息更新成功", data=result)
    except CustomException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        logger.error(f"Failed to update nutrition: {str(e)}")
        return Fail(code=500, msg=f"更新营养信息失败: {str(e)}")
