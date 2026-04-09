import os
import shutil
import uuid
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
    def _calculate_daily_targets(height_cm: int, weight_kg: float, gender: int, age: int) -> Dict:
        if height_cm is None or weight_kg is None or gender is None or age is None:
            raise CustomException(message="缺少用户身体信息，无法计算每日摄入目标", code=422)

        try:
            height_cm = int(height_cm)
            weight_kg = float(weight_kg)
            gender = int(gender)
            age = int(age)
        except Exception as e:
            raise CustomException(message=f"用户身体信息格式错误，无法计算每日摄入目标: {str(e)}", code=422)

        if gender == 1:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        elif gender == 2:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 78

        bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
        bmi_status = "正常"
        if bmi < 18.5:
            bmi_status = "偏瘦"
        elif 24 <= bmi < 28:
            bmi_status = "超重"
        elif bmi >= 28:
            bmi_status = "肥胖"

        activity_factor = 1.375
        calorie_adjust = 0
        if bmi_status == "偏瘦":
            calorie_adjust = 250
        elif bmi_status == "超重":
            calorie_adjust = -300
        elif bmi_status == "肥胖":
            calorie_adjust = -500

        total_calories = int(round(bmr * activity_factor + calorie_adjust))
        if gender == 1:
            total_calories = max(total_calories, 1500)
        elif gender == 2:
            total_calories = max(total_calories, 1200)
        else:
            total_calories = max(total_calories, 1350)

        protein_factor = 1.0
        if bmi_status in {"超重", "肥胖"}:
            protein_factor = 1.2
        elif bmi_status == "偏瘦":
            protein_factor = 1.2
        protein_g = int(round(min(2.0, protein_factor) * weight_kg))
        protein_calories = protein_g * 4

        fat_ratio = 0.28
        fat_calories = total_calories * fat_ratio
        fat_g = int(round(fat_calories / 9))

        remaining_calories = max(0, total_calories - protein_calories - fat_g * 9)
        carb_g = int(round(remaining_calories / 4))
        carb_g = max(carb_g, 130)

        fiber_min_by_sex = 25 if gender != 2 else 21
        fiber_g = int(round(max(fiber_min_by_sex, 14 * total_calories / 1000)))
        sodium_mg = 2000

        return {
            "bmi": bmi,
            "bmi_status": bmi_status,
            "bmr": round(bmr, 1),
            "activity_factor": activity_factor,
            "calorie_adjust": calorie_adjust,
            "targets": {
                "calories": total_calories,
                "protein": protein_g,
                "fat": fat_g,
                "carbs": carb_g,
                "fiber": fiber_g,
                "sodium": sodium_mg,
            },
        }
    
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
            raise CustomException(message="用户不存在", code=404)
            
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
                await RecognitionDetail.create(
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
            total_fiber=total_nutrition["fiber"],
            total_sodium=total_nutrition["sodium"],
            summary=analysis_summary
        )

        logger.info(f"Recognition record {record.id} created for user {user_id}")
        
        # 处理识别详情，转换为前端期望的格式
        details = []
        for result in results:
            food_name_en = result.class_name
            food_name_zh = result.class_name
            try:
                food_obj = await FoodCategory.get_or_none(code=result.class_id)
                if food_obj:
                    food_name_en = food_obj.name
                    food_name_zh = food_obj.chinese_name or food_obj.name
            except Exception:
                pass

            details.append({
                "food_name": food_name_zh,
                "food_name_zh": food_name_zh,
                "food_name_en": food_name_en,
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
                    "food_name": (d.food.chinese_name or d.food.name) if d.food else "Unknown",
                    "food_name_zh": (d.food.chinese_name or d.food.name) if d.food else "Unknown",
                    "food_name_en": d.food.name if d.food else "Unknown",
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
                    "total_fiber": getattr(record.analysis, "total_fiber", 0) or 0,
                    "total_sodium": getattr(record.analysis, "total_sodium", 0) or 0,
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
                "nutrition": nutrition_info,
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
    async def get_nutrition_recommendation(user_id: int, height: int, weight: float, gender: int, age: int) -> Dict:
        """
        根据身体数据生成营养推荐方案
        
        Args:
            user_id: 用户ID
            height: 身高(cm)
            weight: 体重(kg)
            gender: 性别 (1:男, 2:女, 3:其他)
            age: 年龄
            
        Returns:
            Dict: 推荐方案内容
        """
        try:
            # 基础代谢计算 (Mifflin-St Jeor Equation)
            if gender == 1: # 男
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            elif gender == 2: # 女
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
            else: # 其他/平均
                bmr = 10 * weight + 6.25 * height - 5 * age - 78
                
            # 每日推荐总热量 (假设轻微活动量)
            total_calories = round(bmr * 1.375)
            
            # 宏量营养素比例
            protein_calories = total_calories * 0.15
            fat_calories = total_calories * 0.25
            carb_calories = total_calories * 0.60
            
            # 换算成克数
            protein_g = round(protein_calories / 4)
            fat_g = round(fat_calories / 9)
            carb_g = round(carb_calories / 4)
            
            # 计算 BMI
            bmi = round(weight / ((height/100)**2), 1)
            bmi_status = "正常"
            if bmi < 18.5:
                bmi_status = "偏瘦"
            elif 24 <= bmi < 28:
                bmi_status = "超重"
            elif bmi >= 28:
                bmi_status = "肥胖"
            
            # 生成建议文本
            content = (
                f"您的BMI为{bmi}，属于{bmi_status}。建议每日摄入热量约{total_calories}kcal。 "
                f"其中蛋白质约{protein_g}g，脂肪约{fat_g}g，碳水化合物约{carb_g}g。"
            )
            
            # 记录到数据库
            user = await User.get(id=user_id)
            await NutritionRecommendation.create(
                user=user,
                record=None,
                content=content,
                reference=f"BMI: {bmi}, Status: {bmi_status}"
            )
            
            return {
                "bmi": bmi,
                "bmi_status": bmi_status,
                "total_calories": total_calories,
                "protein_g": protein_g,
                "fat_g": fat_g,
                "carb_g": carb_g,
                "content": content
            }
        except Exception as e:
            logger.error(f"Failed to generate recommendation: {str(e)}")
            raise CustomException(message=f"推荐生成失败: {str(e)}", code=500)

    @staticmethod
    async def generate_record_recommendation(record_id: int, user_id: int) -> Dict:
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                raise CustomException(message="用户不存在", code=404)

            try:
                targets_info = FoodController._calculate_daily_targets(
                    height_cm=getattr(user, "height_cm", None),
                    weight_kg=getattr(user, "weight_kg", None),
                    gender=getattr(user, "gender", None),
                    age=getattr(user, "age", None),
                )
            except CustomException as e:
                if e.status_code != 422:
                    raise
                targets_info = {
                    "bmi": None,
                    "bmi_status": "未知",
                    "targets": {
                        "calories": 2000,
                        "protein": 60,
                        "fat": 65,
                        "carbs": 250,
                        "fiber": 25,
                        "sodium": 2000,
                    },
                }

            record = await RecognitionRecord.get_or_none(id=record_id, user_id=user_id).prefetch_related(
                "analysis", "details", "details__food", "details__food__nutrition"
            )
            if not record:
                raise CustomException(message="识别记录不存在", code=404)

            total = {
                "calories": 0.0,
                "protein": 0.0,
                "fat": 0.0,
                "carbs": 0.0,
                "fiber": 0.0,
                "sodium": 0.0,
            }

            if record.analysis:
                total["calories"] = float(record.analysis.total_energy or 0)
                total["protein"] = float(record.analysis.total_protein or 0)
                total["fat"] = float(record.analysis.total_fat or 0)
                total["carbs"] = float(record.analysis.total_carbohydrate or 0)
                total["fiber"] = float(getattr(record.analysis, "total_fiber", 0) or 0)
                total["sodium"] = float(getattr(record.analysis, "total_sodium", 0) or 0)

            item_summaries: List[Dict] = []
            for d in record.details:
                if d.food and d.food.nutrition:
                    n = d.food.nutrition
                    calories = float(n.energy or 0)
                    protein = float(n.protein or 0)
                    carbs = float(n.carbohydrate or 0)
                    fat = float(n.fat or 0)
                    fiber = float(n.fiber or 0)
                    sodium = float(n.sodium or 0)
                    item_summaries.append(
                        {
                            "name_zh": d.food.chinese_name or d.food.name,
                            "name_en": d.food.name,
                            "calories": calories,
                            "protein": protein,
                            "carbs": carbs,
                            "fat": fat,
                            "fiber": fiber,
                            "sodium": sodium,
                        }
                    )

            if total["calories"] == 0 and item_summaries:
                total["calories"] = sum(i["calories"] for i in item_summaries)
                total["protein"] = sum(i["protein"] for i in item_summaries)
                total["carbs"] = sum(i["carbs"] for i in item_summaries)
                total["fat"] = sum(i["fat"] for i in item_summaries)
                total["fiber"] = sum(i["fiber"] for i in item_summaries)
                total["sodium"] = sum(i["sodium"] for i in item_summaries)

            if (total["fiber"] == 0 or total["sodium"] == 0) and item_summaries:
                for d in record.details:
                    if d.food and d.food.nutrition:
                        n = d.food.nutrition
                        total["fiber"] += float(n.fiber or 0)
                        total["sodium"] += float(n.sodium or 0)

            targets = targets_info["targets"]

            tips: List[str] = []
            tips.append("说明：当前识别的营养值按每种食物 100g 估算（未输入重量）。")
            if targets_info.get("bmi") is None:
                tips.append("提示：请先在个人资料完善身高、体重、性别、年龄，可获得更精准的个性化建议。")

            meal_calories = total["calories"]
            if meal_calories <= 0:
                tips.append("本次餐食热量数据不足，建议补充更清晰的图片或完善食物库营养信息。")
                meal_calories = max(0.0, total["protein"] * 4 + total["carbs"] * 4 + total["fat"] * 9)

            daily_calories = float(targets.get("calories") or 0)
            meal_cal_ratio = meal_calories / daily_calories if daily_calories else 0
            if daily_calories:
                tips.append(f"本次餐食约 {round(meal_calories)} kcal，占您全天目标 {daily_calories} kcal 的 {round(meal_cal_ratio * 100)}%。")

            bmi_status = targets_info.get("bmi_status") or "未知"
            if meal_cal_ratio >= 0.6:
                if bmi_status in {"超重", "肥胖"}:
                    tips.append("本次热量占比偏高且体重偏高，建议下一餐减少主食与油脂，优先选择高纤维蔬菜 + 优质蛋白。")
                else:
                    tips.append("本次热量占比偏高，建议下一餐以清淡为主并控制油脂与含糖饮料。")
            elif 0.25 <= meal_cal_ratio < 0.6:
                tips.append("本次热量占比适中，建议继续保持全天均衡分配。")
            elif daily_calories:
                if bmi_status == "偏瘦":
                    tips.append("本次热量占比偏低且体重偏轻，可在下一餐适量增加主食与优质脂肪（坚果、牛油果、橄榄油）。")
                else:
                    tips.append("本次热量占比偏低，若今日其他餐也偏少，可适当补充主食或蛋白以避免能量不足。")

            protein_kcal = total["protein"] * 4
            carb_kcal = total["carbs"] * 4
            fat_kcal = total["fat"] * 9
            kcal_base = meal_calories if meal_calories > 0 else (protein_kcal + carb_kcal + fat_kcal)
            kcal_base = kcal_base if kcal_base > 0 else 1

            protein_pct = protein_kcal / kcal_base
            carb_pct = carb_kcal / kcal_base
            fat_pct = fat_kcal / kcal_base

            if protein_pct < 0.12:
                tips.append("本次蛋白质占比偏低，建议补充鸡蛋、牛奶、豆制品、鱼虾或瘦肉，提升饱腹感与肌肉维持。")
            elif protein_pct > 0.35:
                tips.append("本次蛋白质占比偏高，注意搭配蔬菜与主食，避免膳食结构过于单一。")

            if fat_pct > 0.40:
                tips.append("本次脂肪占比偏高，建议减少煎炸/肥肉/奶油，改用蒸煮炖并控制用油。")
            elif fat_pct < 0.15:
                tips.append("本次脂肪占比偏低，可适量加入坚果、橄榄油或深海鱼，帮助脂溶性维生素吸收。")

            if carb_pct < 0.40:
                tips.append("本次碳水占比偏低，若伴随疲劳或训练，可适量增加全谷物、薯类等优质主食。")
            elif carb_pct > 0.70:
                tips.append("本次碳水占比偏高，建议用全谷物替代精制主食，并搭配蛋白与蔬菜降低血糖波动。")

            fiber_ratio = total["fiber"] / targets["fiber"] if targets["fiber"] else 0
            fiber_density = (total["fiber"] / kcal_base) * 1000 if kcal_base else 0
            if fiber_ratio < 0.6 or fiber_density < 10:
                tips.append("膳食纤维偏低，建议在下一餐增加深色蔬菜、豆类或全谷物，并保证足量饮水。")

            if total["sodium"] > targets["sodium"]:
                tips.append("钠摄入偏高，建议减少咸菜、酱料与加工食品，烹饪少盐。")
            elif total["sodium"] > targets["sodium"] * 0.6:
                tips.append("本次钠占比较高，注意控制蘸料与汤汁摄入，优先选择清蒸/白灼做法。")

            if item_summaries:
                top_sodium = sorted(item_summaries, key=lambda x: x["sodium"], reverse=True)[:2]
                top_sodium_names = [f"{i['name_zh']}({round(i['sodium'])}mg)" for i in top_sodium if i["sodium"] > 0]
                if top_sodium_names:
                    tips.append(f"本次钠主要来源：{ '、'.join(top_sodium_names) }。")

            bmi = targets_info["bmi"]
            if bmi is not None:
                tips.append(f"您的 BMI 为 {bmi}（{bmi_status}），建议结合目标（维持/增重/减脂）长期坚持饮食结构优化与规律运动。")

            content = "\n".join(tips)
            reference = (
                f"record_id={record_id}; BMI={bmi}({bmi_status}); "
                f"cal={round(total['calories'])}/{targets['calories']}; "
                f"protein={round(total['protein'])}/{targets['protein']}; "
                f"fiber={round(total['fiber'])}/{targets['fiber']}; "
                f"sodium={round(total['sodium'])}/{targets['sodium']}"
            )

            await NutritionRecommendation.create(
                user=user,
                record=record,
                content=content,
                reference=reference[:255],
            )

            return {
                "record_id": record_id,
                "targets": targets,
                "total": total,
                "tips": tips,
            }
        except CustomException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate record recommendation: {str(e)}")
            raise CustomException(message=f"生成饮食建议失败: {str(e)}", code=500)
            
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
                await Nutrition.create(
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

