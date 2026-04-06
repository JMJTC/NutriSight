import json
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import UploadFile
from tortoise.expressions import Q

from app.core.exceptions import CustomException
from app.log import logger
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
            predictions, annotated_image_path = yolo_service.predict_with_annotation(file_path)
            # 如果模型未生成标注图，仍保留原图用作展示(避免前端src空导致显示问题)
            if not annotated_image_path and predictions:
                annotated_image_path = relative_path
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
            annotated_image_path=annotated_image_path,
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
                if not food_cat:
                    # 如果数据库没有该类别，则使用 Unknown 备用分类保证外键不为空
                    food_cat = await FoodCategory.get_or_none(code=-1)
                    if not food_cat:
                        food_cat = await FoodCategory.create(name="Unknown", code=-1, description="未知类别")
                
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
            "annotated_image_path": annotated_image_path,
            "details": details,
            "nutrition": nutrition_info,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return response_dict

    @staticmethod
    async def delete_record(record_id: int, user_id: int) -> bool:
        """
        删除识别记录及其关联文件
        
        Args:
            record_id: 识别记录ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            record = await RecognitionRecord.get_or_none(id=record_id, user_id=user_id)
            if not record:
                raise CustomException(message="记录不存在", code=404)
            
            # 删除物理文件
            for path_attr in ["image_path", "annotated_image_path"]:
                relative_path = getattr(record, path_attr)
                if relative_path:
                    # 去掉开头的 /
                    if relative_path.startswith("/"):
                        relative_path = relative_path[1:]
                    
                    full_path = os.path.join(settings.BASE_DIR, "deploy", relative_path)
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                            logger.info(f"Deleted file: {full_path}")
                        except Exception as e:
                            logger.error(f"Failed to delete file {full_path}: {str(e)}")
            
            # 删除记录 (级联删除 details 和 analysis)
            await record.delete()
            logger.info(f"Recognition record {record_id} deleted by user {user_id}")
            return True
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete record: {str(e)}")
            raise CustomException(message=f"删除记录失败: {str(e)}", code=500)

    @staticmethod
    async def delete_records(record_ids: List[int], user_id: int) -> int:
        """
        批量删除识别记录
        
        Args:
            record_ids: 记录ID列表
            user_id: 用户ID
            
        Returns:
            int: 成功删除的数量
        """
        count = 0
        for rid in record_ids:
            try:
                if await FoodController.delete_record(rid, user_id):
                    count += 1
            except Exception as e:
                logger.warning(f"Failed to delete record {rid} in batch: {str(e)}")
        return count

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
                    "annotated_image_path": r.annotated_image_path,
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
                "annotated_image_path": record.annotated_image_path,
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
                    "chinese_name": cat.chinese_name,
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
                chinese_name=category_in.chinese_name,
                code=category_in.code,
                food_type=category_in.food_type,
                description=category_in.description,
                image_url=category_in.image_url
            )
            
            logger.info(f"Food category {category.id} created: {category.name}")
            
            return {
                "id": category.id,
                "name": category.name,
                "chinese_name": category.chinese_name,
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
            if category_in.chinese_name is not None:
                category.chinese_name = category_in.chinese_name
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
                "chinese_name": category.chinese_name,
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
                "food_id": food.id,
                "food_name": food.name,
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

    @staticmethod
    async def get_food_category_detail(category_id: int) -> Dict:
        """
        获取单个食物类别的详细信息，包括营养信息
        
        Args:
            category_id: 食物类别ID
            
        Returns:
            Dict: 食物类别详细信息
        """
        try:
            category = await FoodCategory.get_or_none(id=category_id)
            if not category:
                raise CustomException(message=f"食物类别 {category_id} 不存在", code=404)
            
            result = {
                "id": category.id,
                "name": category.name,
                "code": category.code,
                "food_type": category.food_type,
                "description": category.description,
                "image_url": category.image_url,
                "created_at": category.created_at.isoformat(),
                "updated_at": category.updated_at.isoformat(),
            }
            
            # 获取营养信息
            nutrition = await Nutrition.get_or_none(food=category)
            if nutrition:
                result["nutrition"] = {
                    "id": nutrition.id,
                    "food_id": nutrition.food_id,
                    "food_name": category.name,
                    "energy": nutrition.energy,
                    "protein": nutrition.protein,
                    "fat": nutrition.fat,
                    "carbohydrate": nutrition.carbohydrate,
                    "fiber": nutrition.fiber,
                    "sodium": nutrition.sodium,
                    "created_at": nutrition.created_at.isoformat(),
                    "updated_at": nutrition.updated_at.isoformat(),
                }
            else:
                result["nutrition"] = None
            
            return result
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to get category detail: {str(e)}")
            raise CustomException(message=f"获取食物类别详情失败: {str(e)}", code=500)

    @staticmethod
    async def delete_food_category(category_id: int) -> bool:
        """
        删除食物类别并级联删除关联的营养信息
        
        Args:
            category_id: 食物类别ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            category = await FoodCategory.get_or_none(id=category_id)
            if not category:
                raise CustomException(message=f"食物类别 {category_id} 不存在", code=404)
            
            # 删除关联的营养信息
            nutrition = await Nutrition.get_or_none(food=category)
            if nutrition:
                await nutrition.delete()
                logger.info(f"Deleted nutrition info for food category {category_id}")
            
            # 删除食物类别
            await category.delete()
            logger.info(f"Food category {category_id} deleted")
            
            return True
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete category: {str(e)}")
            raise CustomException(message=f"删除食物类别失败: {str(e)}", code=500)

    @staticmethod
    async def save_food_image(file: UploadFile) -> str:
        """
        保存食物示例图片
        
        Args:
            file: 上传的图片文件
            
        Returns:
            str: 相对路径 URL
        """
        try:
            upload_dir = os.path.join(settings.BASE_DIR, "deploy", "static", "uploads", "food_images")
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            file_ext = file.filename.split(".")[-1] if file.filename else "png"
            file_name = f"{uuid.uuid4()}.{file_ext}"
            file_path = os.path.join(upload_dir, file_name)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            relative_path = f"/static/uploads/food_images/{file_name}"
            logger.info(f"Food image saved: {relative_path}")
            
            return relative_path
        except Exception as e:
            logger.error(f"Failed to save food image: {str(e)}")
            raise CustomException(message=f"图片保存失败: {str(e)}", code=500)

    @staticmethod
    async def get_next_food_code() -> int:
        """
        获取下一个可用的YOLO类别ID（自增）
        
        Returns:
            int: 下一个可用的code值
        """
        try:
            # 获取所有food的code，找到最大值
            all_foods = await FoodCategory.all()
            if all_foods:
                max_code = max([food.code for food in all_foods if isinstance(food.code, int)])
                return max_code + 1
            return 0
        except Exception as e:
            logger.error(f"Error getting next food code: {str(e)}")
            return 0

    @staticmethod
    async def create_food_category_with_file(
        name: str,
        code: Optional[int] = None,
        food_type: Optional[str] = None,
        description: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        nutrition_data: Optional[Dict] = None
    ) -> Dict:
        """
        创建食物类别，支持图片上传和营养信息
        
        Args:
            name: 食物名称
            code: YOLO类别ID（可选，自动生成）
            food_type: 食物类型
            description: 描述
            image_file: 图片文件（可选）
            nutrition_data: 营养信息字典（可选）
            
        Returns:
            Dict: 创建的食物类别信息
        """
        try:
            # 检查name是否已存在
            existing_name = await FoodCategory.get_or_none(name=name)
            if existing_name:
                raise CustomException(message=f"食物名称 {name} 已存在", code=400)
            
            # 如果没有提供code，自动生成
            if code is None or code == "":
                code = await FoodController.get_next_food_code()
                logger.info(f"Auto-generated code for food {name}: {code}")
            else:
                # 如果提供了code，检查是否已存在
                existing_code = await FoodCategory.get_or_none(code=code)
                if existing_code:
                    raise CustomException(message=f"YOLO 类别 ID {code} 已存在", code=400)
            
            # 处理图片上传
            image_url = None
            if image_file:
                image_url = await FoodController.save_food_image(image_file)
            
            # 创建食物类别
            category = await FoodCategory.create(
                name=name,
                code=code,
                food_type=food_type,
                description=description,
                image_url=image_url
            )
            
            # 创建营养信息（如果提供）
            if nutrition_data:
                nutrition = await Nutrition.create(
                    food=category,
                    energy=float(nutrition_data.get("energy", 0)),
                    protein=float(nutrition_data.get("protein", 0)),
                    fat=float(nutrition_data.get("fat", 0)),
                    carbohydrate=float(nutrition_data.get("carbohydrate", 0)),
                    fiber=float(nutrition_data.get("fiber", 0)),
                    sodium=float(nutrition_data.get("sodium", 0))
                )
                logger.info(f"Nutrition info created for food category {category.id}")
            
            logger.info(f"Food category {category.id} created with image: {name}")
            
            return await FoodController.get_food_category_detail(category.id)
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to create category with file: {str(e)}")
            raise CustomException(message=f"创建食物类别失败: {str(e)}", code=500)

    @staticmethod
    async def update_food_category_with_file(
        category_id: int,
        name: Optional[str] = None,
        food_type: Optional[str] = None,
        description: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        image_url: Optional[str] = None,
        nutrition_data: Optional[Dict] = None
    ) -> Dict:
        """
        更新食物类别，支持图片上传和营养信息更新
        
        Args:
            category_id: 食物类别ID
            name: 食物名称
            food_type: 食物类型
            description: 描述
            image_file: 新的图片文件（可选）
            image_url: 图片URL（如果image_file为空则使用此值）
            nutrition_data: 营养信息字典（可选）
            
        Returns:
            Dict: 更新后的食物类别信息
        """
        try:
            category = await FoodCategory.get_or_none(id=category_id)
            if not category:
                raise CustomException(message=f"食物类别 {category_id} 不存在", code=404)
            
            # 检查名称唯一性
            if name and name != category.name:
                existing = await FoodCategory.get_or_none(name=name)
                if existing:
                    raise CustomException(message=f"食物名称 {name} 已存在", code=400)
                category.name = name
            
            # 更新其他字段
            if food_type is not None:
                category.food_type = food_type
            if description is not None:
                category.description = description
            
            # 处理图片上传
            if image_file:
                image_url = await FoodController.save_food_image(image_file)
            if image_url is not None:
                category.image_url = image_url
            
            await category.save()
            
            # 更新营养信息（如果提供）
            if nutrition_data:
                nutrition = await Nutrition.get_or_none(food=category)
                if nutrition:
                    nutrition.energy = float(nutrition_data.get("energy", nutrition.energy))
                    nutrition.protein = float(nutrition_data.get("protein", nutrition.protein))
                    nutrition.fat = float(nutrition_data.get("fat", nutrition.fat))
                    nutrition.carbohydrate = float(nutrition_data.get("carbohydrate", nutrition.carbohydrate))
                    nutrition.fiber = float(nutrition_data.get("fiber", nutrition.fiber))
                    nutrition.sodium = float(nutrition_data.get("sodium", nutrition.sodium))
                    await nutrition.save()
                    logger.info(f"Nutrition info for food {category_id} updated")
                else:
                    # 如果不存在营养信息则创建
                    nutrition = await Nutrition.create(
                        food=category,
                        energy=float(nutrition_data.get("energy", 0)),
                        protein=float(nutrition_data.get("protein", 0)),
                        fat=float(nutrition_data.get("fat", 0)),
                        carbohydrate=float(nutrition_data.get("carbohydrate", 0)),
                        fiber=float(nutrition_data.get("fiber", 0)),
                        sodium=float(nutrition_data.get("sodium", 0))
                    )
                    logger.info(f"Nutrition info created for food {category_id}")
            
            logger.info(f"Food category {category_id} updated")
            
            return await FoodController.get_food_category_detail(category.id)
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to update category with file: {str(e)}")
            raise CustomException(message=f"更新食物类别失败: {str(e)}", code=500)

