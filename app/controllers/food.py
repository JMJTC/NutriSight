import json
import os
import shutil
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import UploadFile
from tortoise.expressions import Q

from app.core.exceptions import CustomException
from app.models.food import (
    FoodCategory,
    Nutrition,
    RecognitionRecord,
    RecognitionDetail,
    NutritionAnalysis,
    NutritionRecommendation,
    UserProfile
)
from app.schemas.food import (
    RecognitionResponse, 
    RecognitionResult, 
    NutritionBase,
    FoodCategoryCreate,
    FoodCategoryUpdate,
    NutritionCreate,
)
from app.services.yolo_service import yolo_service
from app.settings.config import settings
from app.models.admin import User

logger = logging.getLogger(__name__)


class FoodController:
    """食物识别业务控制器"""
    
    @staticmethod
    async def recognize_food(file: UploadFile, user_id: int) -> RecognitionResponse:
        """
        识别上传的食物图片
        
        Args:
            file: 上传的图片文件
            user_id: 用户ID
            
        Returns:
            RecognitionResponse: 识别结果响应
        """
        # 1. 保存图片文件
        upload_dir = os.path.join(settings.BASE_DIR, "deploy", "static", "uploads")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_ext = file.filename.split(".")[-1] if file.filename else "png"
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, file_name)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"File save failed: {str(e)}")
            raise CustomException(message=f"文件保存失败: {str(e)}", code=500)
        
        # 相对路径用于 URL 访问
        relative_path = f"/static/uploads/{file_name}"

        # 2. 执行 YOLO 推理
        try:
            if not yolo_service.is_ready():
                raise CustomException(message="YOLO 模型未就绪，请检查模型文件", code=500)
            predictions = yolo_service.predict(file_path)
            logger.info(f"YOLO prediction returned {len(predictions)} results")
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Model inference failed: {str(e)}")
            raise CustomException(message=f"模型推理失败: {str(e)}", code=500)

        # 3. 保存识别记录
        try:
            user = await User.get(id=user_id)
        except Exception as e:
            logger.error(f"User not found: {str(e)}")
            raise CustomException(message=f"用户不存在", code=404)
            
        record = await RecognitionRecord.create(
            user=user,
            image_path=relative_path,
            status="success" if predictions else "failed"
        )

        results = []
        total_nutrition = {
            "energy": 0.0,
            "protein": 0.0,
            "fat": 0.0,
            "carbohydrate": 0.0,
            "fiber": 0.0,
            "sodium": 0.0
        }

        # 4. 处理预测结果并聚合营养信息
        for pred in predictions:
            try:
                # 根据 YOLO class_id 查找食物类别
                food_cat = await FoodCategory.get_or_none(code=pred["class_id"])
                
                nutrition_data = None
                if food_cat:
                    nutrition = await Nutrition.get_or_none(food=food_cat)
                    if nutrition:
                        nutrition_data = NutritionBase(
                            energy=nutrition.energy,
                            protein=nutrition.protein,
                            fat=nutrition.fat,
                            carbohydrate=nutrition.carbohydrate,
                            fiber=nutrition.fiber,
                            sodium=nutrition.sodium
                        )
                        # 聚合营养数据（假设每次检测为 100g 或 1 份）
                        # TODO: 可以通过 bbox 面积估算食物重量或份数
                        total_nutrition["energy"] += nutrition.energy
                        total_nutrition["protein"] += nutrition.protein
                        total_nutrition["fat"] += nutrition.fat
                        total_nutrition["carbohydrate"] += nutrition.carbohydrate
                        total_nutrition["fiber"] += nutrition.fiber
                        total_nutrition["sodium"] += nutrition.sodium

                # 保存识别详情
                detail = await RecognitionDetail.create(
                    record=record,
                    food=food_cat if food_cat else None,
                    confidence=pred["confidence"],
                    bbox=pred["bbox"]
                )

                results.append(RecognitionResult(
                    class_id=pred["class_id"],
                    class_name=pred["class_name"] if food_cat is None else food_cat.name,
                    confidence=pred["confidence"],
                    bbox=pred["bbox"],
                    nutrition=nutrition_data
                ))
            except Exception as e:
                logger.error(f"Failed to process prediction {pred}: {str(e)}")
                continue

        # 5. 保存营养分析结果
        analysis_summary = f"识别到 {len(predictions)} 项食物。"
        if total_nutrition["energy"] > 800:
            analysis_summary += " 这是一顿高热量餐食。"
        elif total_nutrition["energy"] > 500:
            analysis_summary += " 这是一顿中等热量餐食。"
        else:
            analysis_summary += " 这是一顿低热量餐食。"
        
        await NutritionAnalysis.create(
            record=record,
            total_energy=total_nutrition["energy"],
            total_protein=total_nutrition["protein"],
            total_fat=total_nutrition["fat"],
            total_carbohydrate=total_nutrition["carbohydrate"],
            summary=analysis_summary
        )

        logger.info(f"Recognition record {record.id} created for user {user_id}")
        
        # 处理识别详情，转换为前端期望的格式
        details = []
        for result in results:
            details.append({
                "food_name": result.class_name,
                "class_id": result.class_id,
                "confidence": result.confidence,
                "count": 1,  # 每个识别结果默认数量为1
                "box": result.bbox,
                "nutrition": {
                    "calories": result.nutrition.energy if result.nutrition else 0,
                    "protein": result.nutrition.protein if result.nutrition else 0,
                    "carbs": result.nutrition.carbohydrate if result.nutrition else 0,
                    "fat": result.nutrition.fat if result.nutrition else 0,
                    "fiber": result.nutrition.fiber if result.nutrition else 0,
                    "sodium": result.nutrition.sodium if result.nutrition else 0,
                } if result.nutrition else {
                    "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sodium": 0
                }
            })
        
        # 转换营养数据格式为前端期望的格式
        nutrition_info = {
            "total_calories": total_nutrition["energy"],
            "total_protein": total_nutrition["protein"],
            "total_carbs": total_nutrition["carbohydrate"],
            "total_fat": total_nutrition["fat"],
            "total_fiber": total_nutrition["fiber"],
            "total_sodium": total_nutrition["sodium"],
        }
        
        # 将响应对象转换为字典以便 JSON 序列化，使用前端期望的格式
        response_dict = {
            "record_id": record.id,
            "image_path": relative_path,
            "details": details,
            "nutrition": nutrition_info,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return response_dict

    @staticmethod
    async def get_history(user_id: int, page: int = 1, page_size: int = 10) -> Dict:
        """
        获取用户的识别历史
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 包含 total, items, page, page_size 的字典
        """
        try:
            offset = (page - 1) * page_size
            records = await RecognitionRecord.filter(
                user_id=user_id
            ).offset(offset).limit(page_size).order_by("-created_at").prefetch_related("analysis")
            
            count = await RecognitionRecord.filter(user_id=user_id).count()
            
            data = []
            for r in records:
                data.append({
                    "id": r.id,
                    "image_path": r.image_path,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": r.status,
                    "total_energy": r.analysis.total_energy if r.analysis else 0,
                })
                
            return {"total": count, "items": data, "page": page, "page_size": page_size}
        except Exception as e:
            logger.error(f"Failed to get history: {str(e)}")
            raise CustomException(message=f"获取历史记录失败: {str(e)}", code=500)

    @staticmethod
    async def get_record_detail(record_id: int, user_id: int) -> RecognitionResponse:
        """
        获取单条识别记录的详细信息
        
        Args:
            record_id: 识别记录ID
            user_id: 用户ID
            
        Returns:
            RecognitionResponse: 识别结果详情
        """
        try:
            record = await RecognitionRecord.get_or_none(
                id=record_id, 
                user_id=user_id
            ).prefetch_related("details", "details__food", "analysis", "details__food__nutrition")
            
            if not record:
                raise CustomException(message="识别记录不存在", code=404)
            
            # 处理识别详情，转换为前端期望的格式
            details = []
            for d in record.details:
                nut_dict = {}
                if d.food and d.food.nutrition:
                    n = d.food.nutrition
                    nut_dict = {
                        "calories": n.energy,
                        "protein": n.protein,
                        "carbs": n.carbohydrate,
                        "fat": n.fat,
                        "fiber": n.fiber,
                        "sodium": n.sodium,
                    }
                else:
                    nut_dict = {
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0,
                        "fiber": 0,
                        "sodium": 0,
                    }
                
                details.append({
                    "id": d.id,
                    "food_name": d.food.name if d.food else "Unknown",
                    "class_id": d.food.code if d.food else -1,
                    "confidence": d.confidence,
                    "count": 1,
                    "box": d.bbox,
                    "nutrition": nut_dict
                })
            
            # 转换营养数据格式为前端期望的格式
            nutrition_info = {}
            if record.analysis:
                nutrition_info = {
                    "total_calories": record.analysis.total_energy,
                    "total_protein": record.analysis.total_protein,
                    "total_carbs": record.analysis.total_carbohydrate,
                    "total_fat": record.analysis.total_fat,
                    "total_fiber": 0,
                    "total_sodium": 0,
                }
            else:
                nutrition_info = {
                    "total_calories": 0,
                    "total_protein": 0,
                    "total_carbs": 0,
                    "total_fat": 0,
                    "total_fiber": 0,
                    "total_sodium": 0,
                }
            
            # 返回前端期望的格式
            return {
                "record_id": record.id,
                "image_path": record.image_path,
                "details": details,
                "analysis": nutrition_info,
                "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to get record detail: {str(e)}")
            raise CustomException(message=f"获取记录详情失败: {str(e)}", code=500)

    @staticmethod
    async def get_food_categories(page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict:
        """
        获取食物类别列表
        
        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词
            
        Returns:
            Dict: 包含类别列表的字典
        """
        try:
            query = Q()
            if search:
                query &= Q(name__contains=search)
                
            offset = (page - 1) * page_size
            categories = await FoodCategory.filter(query).offset(offset).limit(page_size).order_by("code")
            count = await FoodCategory.filter(query).count()
            
            data = []
            for cat in categories:
                cat_dict = {
                    "id": cat.id,
                    "name": cat.name,
                    "code": cat.code,
                    "food_type": cat.food_type,
                    "description": cat.description,
                    "image_url": cat.image_url,
                }
                # 获取营养信息
                nutrition = await Nutrition.get_or_none(food=cat)
                if nutrition:
                    cat_dict["nutrition"] = {
                        "energy": nutrition.energy,
                        "protein": nutrition.protein,
                        "fat": nutrition.fat,
                        "carbohydrate": nutrition.carbohydrate,
                        "fiber": nutrition.fiber,
                        "sodium": nutrition.sodium,
                    }
                data.append(cat_dict)
            
            return {"total": count, "items": data}
        except Exception as e:
            logger.error(f"Failed to get categories: {str(e)}")
            raise CustomException(message=f"获取食物类别失败: {str(e)}", code=500)

    @staticmethod
    async def create_food_category(category_in: FoodCategoryCreate) -> Dict:
        """
        创建新的食物类别
        
        Args:
            category_in: 食物类别创建数据
            
        Returns:
            Dict: 创建的类别信息
        """
        try:
            # 检查 code 是否已存在
            existing = await FoodCategory.get_or_none(code=category_in.code)
            if existing:
                raise CustomException(message=f"YOLO 类别 ID {category_in.code} 已存在", code=400)
            
            # 检查名称是否已存在
            existing_name = await FoodCategory.get_or_none(name=category_in.name)
            if existing_name:
                raise CustomException(message=f"食物名称 {category_in.name} 已存在", code=400)
            
            category = await FoodCategory.create(
                name=category_in.name,
                code=category_in.code,
                food_type=category_in.food_type,
                description=category_in.description,
                image_url=category_in.image_url
            )
            
            logger.info(f"Food category {category.id} created: {category.name}")
            
            return {
                "id": category.id,
                "name": category.name,
                "code": category.code,
                "food_type": category.food_type,
                "description": category.description,
                "image_url": category.image_url,
            }
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to create category: {str(e)}")
            raise CustomException(message=f"创建食物类别失败: {str(e)}", code=500)

    @staticmethod
    async def update_food_category(category_id: int, category_in: FoodCategoryUpdate) -> Dict:
        """
        更新食物类别信息
        
        Args:
            category_id: 类别ID
            category_in: 更新数据
            
        Returns:
            Dict: 更新后的类别信息
        """
        try:
            category = await FoodCategory.get_or_none(id=category_id)
            if not category:
                raise CustomException(message=f"食物类别 {category_id} 不存在", code=404)
            
            # 检查名称唯一性
            if category_in.name and category_in.name != category.name:
                existing = await FoodCategory.get_or_none(name=category_in.name)
                if existing:
                    raise CustomException(message=f"食物名称 {category_in.name} 已存在", code=400)
            
            # 更新字段
            if category_in.name is not None:
                category.name = category_in.name
            if category_in.food_type is not None:
                category.food_type = category_in.food_type
            if category_in.description is not None:
                category.description = category_in.description
            if category_in.image_url is not None:
                category.image_url = category_in.image_url
                
            await category.save()
            
            logger.info(f"Food category {category_id} updated")
            
            return {
                "id": category.id,
                "name": category.name,
                "code": category.code,
                "food_type": category.food_type,
                "description": category.description,
                "image_url": category.image_url,
            }
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to update category: {str(e)}")
            raise CustomException(message=f"更新食物类别失败: {str(e)}", code=500)

    @staticmethod
    async def add_nutrition_info(nutrition_in: NutritionCreate) -> Dict:
        """
        为食物类别添加或更新营养信息
        
        Args:
            nutrition_in: 营养信息创建数据
            
        Returns:
            Dict: 保存的营养信息
        """
        try:
            # 检查食物是否存在
            food = await FoodCategory.get_or_none(id=nutrition_in.food_id)
            if not food:
                raise CustomException(message=f"食物类别 {nutrition_in.food_id} 不存在", code=404)
            
            # 检查是否已有营养信息
            nutrition = await Nutrition.get_or_none(food=food)
            if nutrition:
                # 更新现有数据
                nutrition.energy = nutrition_in.energy
                nutrition.protein = nutrition_in.protein
                nutrition.fat = nutrition_in.fat
                nutrition.carbohydrate = nutrition_in.carbohydrate
                nutrition.fiber = nutrition_in.fiber
                nutrition.sodium = nutrition_in.sodium
                await nutrition.save()
                logger.info(f"Nutrition info for food {nutrition_in.food_id} updated")
            else:
                # 创建新数据
                nutrition = await Nutrition.create(
                    food=food,
                    energy=nutrition_in.energy,
                    protein=nutrition_in.protein,
                    fat=nutrition_in.fat,
                    carbohydrate=nutrition_in.carbohydrate,
                    fiber=nutrition_in.fiber,
                    sodium=nutrition_in.sodium
                )
                logger.info(f"Nutrition info for food {nutrition_in.food_id} created")
            
            return {
                "food_id": nutrition.food.id,
                "food_name": nutrition.food.name,
                "energy": nutrition.energy,
                "protein": nutrition.protein,
                "fat": nutrition.fat,
                "carbohydrate": nutrition.carbohydrate,
                "fiber": nutrition.fiber,
                "sodium": nutrition.sodium,
            }
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to add nutrition info: {str(e)}")
            raise CustomException(message=f"保存营养信息失败: {str(e)}", code=500)

    @staticmethod
    async def get_service_status() -> Dict:
        """
        获取服务状态信息
        
        Returns:
            Dict: 服务状态信息
        """
        try:
            yolo_status = yolo_service.get_status()
            
            # 获取数据库统计
            total_categories = await FoodCategory.all().count()
            total_records = await RecognitionRecord.all().count()
            
            return {
                "yolo_model": yolo_status,
                "database": {
                    "total_categories": total_categories,
                    "total_records": total_records,
                },
                "status": "ready" if yolo_status["ready"] else "not_ready"
            }
        except Exception as e:
            logger.error(f"Failed to get service status: {str(e)}")
            return {
                "yolo_model": {
                    "ready": False,
                    "error": str(e)
                },
                "database": {"error": str(e)},
                "status": "error"
            }

