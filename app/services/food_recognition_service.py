import asyncio
import io
import os
import uuid
from typing import Dict, List, Optional

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.exceptions import CustomException
from app.log import logger
from app.models.admin import User
from app.models.food import (
    FoodCategory,
    Nutrition,
    NutritionAnalysis,
    NutritionRecommendation,
    RecognitionDetail,
    RecognitionRecord,
)
from app.schemas.food import NutritionBase, RecognitionResponse, RecognitionResult
from app.services.yolo_service import yolo_service
from app.settings.config import settings


class FoodRecognitionService:
    """食物识别、历史记录与营养推荐服务。"""

    ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    ALLOWED_IMAGE_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/bmp",
        "image/webp",
        "application/octet-stream",
    }
    MAX_UPLOAD_IMAGE_SIZE = 8 * 1024 * 1024
    MAX_UPLOAD_IMAGE_PIXELS = 20_000_000

    async def _validate_image_upload(self, file: UploadFile) -> tuple[bytes, str]:
        """校验上传图片的类型、大小和内容。"""
        filename = (file.filename or "").strip()
        if not filename:
            raise CustomException(message="图片文件名不能为空", code=400)

        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.ALLOWED_IMAGE_EXTENSIONS:
            raise CustomException(
                message="仅支持 jpg、jpeg、png、bmp、webp 格式的图片",
                code=400,
            )

        content_type = (file.content_type or "").lower()
        if content_type and content_type not in self.ALLOWED_IMAGE_CONTENT_TYPES:
            raise CustomException(message="上传文件不是受支持的图片类型", code=400)

        file_bytes = await file.read(self.MAX_UPLOAD_IMAGE_SIZE + 1)
        if not file_bytes:
            raise CustomException(message="上传图片不能为空", code=400)

        if len(file_bytes) > self.MAX_UPLOAD_IMAGE_SIZE:
            raise CustomException(message="图片大小不能超过 8MB", code=400)

        try:
            with Image.open(io.BytesIO(file_bytes)) as image:
                image.verify()
            with Image.open(io.BytesIO(file_bytes)) as image:
                width, height = image.size
                if width <= 0 or height <= 0:
                    raise CustomException(message="图片尺寸无效", code=400)
                if width * height > self.MAX_UPLOAD_IMAGE_PIXELS:
                    raise CustomException(message="图片分辨率过高，请压缩后重试", code=400)
        except CustomException:
            raise
        except (UnidentifiedImageError, OSError) as exc:
            raise CustomException(message=f"无法解析图片内容: {str(exc)}", code=400)

        return file_bytes, file_ext.lstrip(".")

    @staticmethod
    def _save_upload_bytes(file_bytes: bytes, file_path: str) -> None:
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

    @staticmethod
    def _safe_delete_file(file_path: Optional[str]) -> None:
        if not file_path:
            return
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as exc:
            logger.warning(f"Failed to cleanup file {file_path}: {str(exc)}")

    @staticmethod
    def _calculate_daily_targets(height_cm: int, weight_kg: float, gender: int, age: int) -> Dict:
        if height_cm is None or weight_kg is None or gender is None or age is None:
            raise CustomException(message="缺少用户身体信息，无法计算每日摄入目标", code=422)

        try:
            height_cm = int(height_cm)
            weight_kg = float(weight_kg)
            gender = int(gender)
            age = int(age)
        except Exception as exc:
            raise CustomException(message=f"用户身体信息格式错误，无法计算每日摄入目标: {str(exc)}", code=422)

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

        protein_factor = 1.2 if bmi_status in {"偏瘦", "超重", "肥胖"} else 1.0
        protein_g = int(round(min(2.0, protein_factor) * weight_kg))
        protein_calories = protein_g * 4

        fat_ratio = 0.28
        fat_calories = total_calories * fat_ratio
        fat_g = int(round(fat_calories / 9))

        remaining_calories = max(0, total_calories - protein_calories - fat_g * 9)
        carb_g = max(int(round(remaining_calories / 4)), 130)

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

    async def recognize_food(self, file: UploadFile, user_id: int) -> RecognitionResponse:
        """识别上传的食物图片并生成识别记录。"""
        file_bytes, file_ext = await self._validate_image_upload(file)

        upload_dir = os.path.join(settings.BASE_DIR, "deploy", "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, file_name)
        annotated_full_path = None

        try:
            await asyncio.to_thread(self._save_upload_bytes, file_bytes, file_path)
        except Exception as exc:
            logger.error(f"File save failed: {str(exc)}")
            raise CustomException(message=f"文件保存失败: {str(exc)}", code=500)

        relative_path = f"/static/uploads/{file_name}"

        try:
            predictions, annotated_image_path = await asyncio.to_thread(
                yolo_service.predict_with_annotation,
                file_path,
            )
            if not annotated_image_path and predictions:
                annotated_image_path = relative_path
            if annotated_image_path and annotated_image_path.startswith("/static/uploads/"):
                annotated_file_name = annotated_image_path.replace("/static/uploads/", "", 1)
                annotated_full_path = os.path.join(upload_dir, annotated_file_name)
            logger.info(f"YOLO prediction returned {len(predictions)} results")
        except CustomException:
            self._safe_delete_file(file_path)
            self._safe_delete_file(annotated_full_path)
            raise
        except Exception as exc:
            logger.error(f"Model inference failed: {str(exc)}")
            self._safe_delete_file(file_path)
            self._safe_delete_file(annotated_full_path)
            raise CustomException(message=f"模型推理失败: {str(exc)}", code=500)

        try:
            user = await User.get(id=user_id)
        except Exception as exc:
            logger.error(f"User not found: {str(exc)}")
            self._safe_delete_file(file_path)
            self._safe_delete_file(annotated_full_path)
            raise CustomException(message="用户不存在", code=404)

        record = await RecognitionRecord.create(
            user=user,
            image_path=relative_path,
            annotated_image_path=annotated_image_path,
            status="success" if predictions else "failed",
        )

        results = []
        total_nutrition = {
            "energy": 0.0,
            "protein": 0.0,
            "fat": 0.0,
            "carbohydrate": 0.0,
            "fiber": 0.0,
            "sodium": 0.0,
        }

        for pred in predictions:
            try:
                food_cat = await FoodCategory.get_or_none(code=pred["class_id"])
                if not food_cat:
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
                            sodium=nutrition.sodium,
                        )
                        total_nutrition["energy"] += nutrition.energy
                        total_nutrition["protein"] += nutrition.protein
                        total_nutrition["fat"] += nutrition.fat
                        total_nutrition["carbohydrate"] += nutrition.carbohydrate
                        total_nutrition["fiber"] += nutrition.fiber
                        total_nutrition["sodium"] += nutrition.sodium

                await RecognitionDetail.create(
                    record=record,
                    food=food_cat if food_cat else None,
                    confidence=pred["confidence"],
                    bbox=pred["bbox"],
                )

                results.append(
                    RecognitionResult(
                        class_id=pred["class_id"],
                        class_name=pred["class_name"] if food_cat is None else food_cat.name,
                        confidence=pred["confidence"],
                        bbox=pred["bbox"],
                        nutrition=nutrition_data,
                    )
                )
            except Exception as exc:
                logger.error(f"Failed to process prediction {pred}: {str(exc)}")
                continue

        best_result = max(results, key=lambda item: float(item.confidence or 0), default=None)
        if best_result and best_result.nutrition:
            total_nutrition = {
                "energy": float(best_result.nutrition.energy or 0),
                "protein": float(best_result.nutrition.protein or 0),
                "fat": float(best_result.nutrition.fat or 0),
                "carbohydrate": float(best_result.nutrition.carbohydrate or 0),
                "fiber": float(best_result.nutrition.fiber or 0),
                "sodium": float(best_result.nutrition.sodium or 0),
            }
        else:
            total_nutrition = {
                "energy": 0.0,
                "protein": 0.0,
                "fat": 0.0,
                "carbohydrate": 0.0,
                "fiber": 0.0,
                "sodium": 0.0,
            }

        analysis_summary = "未识别到食物。"
        if best_result:
            analysis_summary = f"识别到食物：{best_result.class_name}（置信度 {(best_result.confidence * 100):.1f}%）。"
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
            summary=analysis_summary,
        )

        logger.info(f"Recognition record {record.id} created for user {user_id}")

        details = []
        results_for_response = sorted(results, key=lambda item: float(item.confidence or 0), reverse=True)
        for result in results_for_response:
            food_name_en = result.class_name
            food_name_zh = result.class_name
            try:
                food_obj = await FoodCategory.get_or_none(code=result.class_id)
                if food_obj:
                    food_name_en = food_obj.name
                    food_name_zh = food_obj.chinese_name or food_obj.name
            except Exception:
                pass

            details.append(
                {
                    "food_name": food_name_zh,
                    "food_name_zh": food_name_zh,
                    "food_name_en": food_name_en,
                    "class_id": result.class_id,
                    "confidence": result.confidence,
                    "count": 1,
                    "box": result.bbox,
                    "nutrition": {
                        "calories": result.nutrition.energy if result.nutrition else 0,
                        "protein": result.nutrition.protein if result.nutrition else 0,
                        "carbs": result.nutrition.carbohydrate if result.nutrition else 0,
                        "fat": result.nutrition.fat if result.nutrition else 0,
                        "fiber": result.nutrition.fiber if result.nutrition else 0,
                        "sodium": result.nutrition.sodium if result.nutrition else 0,
                    }
                    if result.nutrition
                    else {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sodium": 0},
                }
            )

        nutrition_info = {
            "total_calories": total_nutrition["energy"],
            "total_protein": total_nutrition["protein"],
            "total_carbs": total_nutrition["carbohydrate"],
            "total_fat": total_nutrition["fat"],
            "total_fiber": total_nutrition["fiber"],
            "total_sodium": total_nutrition["sodium"],
        }

        return {
            "record_id": record.id,
            "image_path": relative_path,
            "annotated_image_path": annotated_image_path,
            "details": details,
            "nutrition": nutrition_info,
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    async def delete_record(self, record_id: int, user_id: int) -> bool:
        """删除识别记录及其关联文件。"""
        try:
            record = await RecognitionRecord.get_or_none(id=record_id, user_id=user_id)
            if not record:
                raise CustomException(message="记录不存在", code=404)

            for path_attr in ["image_path", "annotated_image_path"]:
                relative_path = getattr(record, path_attr)
                if relative_path:
                    if relative_path.startswith("/"):
                        relative_path = relative_path[1:]

                    full_path = os.path.join(settings.BASE_DIR, "deploy", relative_path)
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                            logger.info(f"Deleted file: {full_path}")
                        except Exception as exc:
                            logger.error(f"Failed to delete file {full_path}: {str(exc)}")

            await record.delete()
            logger.info(f"Recognition record {record_id} deleted by user {user_id}")
            return True
        except CustomException:
            raise
        except Exception as exc:
            logger.error(f"Failed to delete record: {str(exc)}")
            raise CustomException(message=f"删除记录失败: {str(exc)}", code=500)

    async def delete_records(self, record_ids: List[int], user_id: int) -> int:
        """批量删除识别记录。"""
        count = 0
        for record_id in record_ids:
            try:
                if await self.delete_record(record_id, user_id):
                    count += 1
            except Exception as exc:
                logger.warning(f"Failed to delete record {record_id} in batch: {str(exc)}")
        return count

    async def get_history(self, user_id: int, page: int = 1, page_size: int = 10) -> Dict:
        """获取用户的识别历史。"""
        try:
            offset = (page - 1) * page_size
            records = await RecognitionRecord.filter(user_id=user_id).offset(offset).limit(page_size).order_by(
                "-created_at"
            ).prefetch_related("analysis")
            count = await RecognitionRecord.filter(user_id=user_id).count()

            data = []
            for record in records:
                data.append(
                    {
                        "id": record.id,
                        "image_path": record.image_path,
                        "annotated_image_path": record.annotated_image_path,
                        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": record.status,
                        "total_energy": record.analysis.total_energy if record.analysis else 0,
                    }
                )

            return {"total": count, "items": data, "page": page, "page_size": page_size}
        except Exception as exc:
            logger.error(f"Failed to get history: {str(exc)}")
            raise CustomException(message=f"获取历史记录失败: {str(exc)}", code=500)

    async def get_record_detail(self, record_id: int, user_id: int) -> RecognitionResponse:
        """获取单条识别记录的详细信息。"""
        try:
            record = await RecognitionRecord.get_or_none(id=record_id, user_id=user_id).prefetch_related(
                "details",
                "details__food",
                "analysis",
                "details__food__nutrition",
            )

            if not record:
                raise CustomException(message="识别记录不存在", code=404)

            details = []
            best_detail = None
            if record.details:
                best_detail = max(record.details, key=lambda item: float(getattr(item, "confidence", 0) or 0))
            details_for_response = [best_detail] if best_detail else []

            for detail in details_for_response:
                if detail.food and detail.food.nutrition:
                    nutrition = detail.food.nutrition
                    nut_dict = {
                        "calories": nutrition.energy,
                        "protein": nutrition.protein,
                        "carbs": nutrition.carbohydrate,
                        "fat": nutrition.fat,
                        "fiber": nutrition.fiber,
                        "sodium": nutrition.sodium,
                    }
                else:
                    nut_dict = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sodium": 0}

                details.append(
                    {
                        "id": detail.id,
                        "food_name": (detail.food.chinese_name or detail.food.name) if detail.food else "Unknown",
                        "food_name_zh": (detail.food.chinese_name or detail.food.name) if detail.food else "Unknown",
                        "food_name_en": detail.food.name if detail.food else "Unknown",
                        "class_id": detail.food.code if detail.food else -1,
                        "confidence": detail.confidence,
                        "count": 1,
                        "box": detail.bbox,
                        "nutrition": nut_dict,
                    }
                )

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

            return {
                "record_id": record.id,
                "image_path": record.image_path,
                "annotated_image_path": record.annotated_image_path,
                "details": details,
                "analysis": nutrition_info,
                "nutrition": nutrition_info,
                "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        except CustomException:
            raise
        except Exception as exc:
            logger.error(f"Failed to get record detail: {str(exc)}")
            raise CustomException(message=f"获取记录详情失败: {str(exc)}", code=500)

    async def get_service_status(self) -> Dict:
        """获取 YOLO 服务与数据库状态。"""
        try:
            yolo_status = await asyncio.to_thread(yolo_service.get_status)
            total_categories = await FoodCategory.all().count()
            total_records = await RecognitionRecord.all().count()

            return {
                "yolo_model": yolo_status,
                "database": {
                    "total_categories": total_categories,
                    "total_records": total_records,
                },
                "status": "ready" if yolo_status["ready"] else "not_ready",
            }
        except Exception as exc:
            logger.error(f"Failed to get service status: {str(exc)}")
            return {
                "yolo_model": {"ready": False, "error": str(exc)},
                "database": {"error": str(exc)},
                "status": "error",
            }

    async def get_nutrition_recommendation(
        self,
        user_id: int,
        height: int,
        weight: float,
        gender: int,
        age: int,
    ) -> Dict:
        """根据身体数据生成营养推荐方案。"""
        try:
            if gender == 1:
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            elif gender == 2:
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
            else:
                bmr = 10 * weight + 6.25 * height - 5 * age - 78

            total_calories = round(bmr * 1.375)
            protein_calories = total_calories * 0.15
            fat_calories = total_calories * 0.25
            carb_calories = total_calories * 0.60

            protein_g = round(protein_calories / 4)
            fat_g = round(fat_calories / 9)
            carb_g = round(carb_calories / 4)

            bmi = round(weight / ((height / 100) ** 2), 1)
            bmi_status = "正常"
            if bmi < 18.5:
                bmi_status = "偏瘦"
            elif 24 <= bmi < 28:
                bmi_status = "超重"
            elif bmi >= 28:
                bmi_status = "肥胖"

            content = (
                f"您的BMI为{bmi}，属于{bmi_status}。建议每日摄入热量约{total_calories}kcal。 "
                f"其中蛋白质约{protein_g}g，脂肪约{fat_g}g，碳水化合物约{carb_g}g。"
            )

            user = await User.get(id=user_id)
            await NutritionRecommendation.create(
                user=user,
                record=None,
                content=content,
                reference=f"BMI: {bmi}, Status: {bmi_status}",
            )

            return {
                "bmi": bmi,
                "bmi_status": bmi_status,
                "total_calories": total_calories,
                "protein_g": protein_g,
                "fat_g": fat_g,
                "carb_g": carb_g,
                "content": content,
            }
        except Exception as exc:
            logger.error(f"Failed to generate recommendation: {str(exc)}")
            raise CustomException(message=f"推荐生成失败: {str(exc)}", code=500)

    async def generate_record_recommendation(self, record_id: int, user_id: int) -> Dict:
        """根据识别记录生成饮食建议。"""
        try:
            user = await User.get_or_none(id=user_id)
            if not user:
                raise CustomException(message="用户不存在", code=404)

            try:
                targets_info = self._calculate_daily_targets(
                    height_cm=getattr(user, "height_cm", None),
                    weight_kg=getattr(user, "weight_kg", None),
                    gender=getattr(user, "gender", None),
                    age=getattr(user, "age", None),
                )
            except CustomException as exc:
                if exc.status_code != 422:
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
                "analysis",
                "details",
                "details__food",
                "details__food__nutrition",
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

            best_detail = None
            if record.details:
                best_detail = max(record.details, key=lambda item: float(getattr(item, "confidence", 0) or 0))

            item_summaries: List[Dict] = []
            if best_detail and best_detail.food and best_detail.food.nutrition:
                nutrition = best_detail.food.nutrition
                item_summaries.append(
                    {
                        "name_zh": best_detail.food.chinese_name or best_detail.food.name,
                        "name_en": best_detail.food.name,
                        "calories": float(nutrition.energy or 0),
                        "protein": float(nutrition.protein or 0),
                        "carbs": float(nutrition.carbohydrate or 0),
                        "fat": float(nutrition.fat or 0),
                        "fiber": float(nutrition.fiber or 0),
                        "sodium": float(nutrition.sodium or 0),
                    }
                )

            if total["calories"] == 0 and item_summaries:
                total["calories"] = sum(item["calories"] for item in item_summaries)
                total["protein"] = sum(item["protein"] for item in item_summaries)
                total["carbs"] = sum(item["carbs"] for item in item_summaries)
                total["fat"] = sum(item["fat"] for item in item_summaries)
                total["fiber"] = sum(item["fiber"] for item in item_summaries)
                total["sodium"] = sum(item["sodium"] for item in item_summaries)

            if (total["fiber"] == 0 or total["sodium"] == 0) and item_summaries:
                total["fiber"] = float(item_summaries[0]["fiber"] or 0)
                total["sodium"] = float(item_summaries[0]["sodium"] or 0)

            targets = targets_info["targets"]
            tips: List[str] = ["说明：当前识别的营养值按每种食物 100g 估算（未输入重量）。"]
            if targets_info.get("bmi") is None:
                tips.append("提示：请先在个人资料完善身高、体重、性别、年龄，可获得更精准的个性化建议。")

            meal_calories = total["calories"]
            if meal_calories <= 0:
                tips.append("本次餐食热量数据不足，建议补充更清晰的图片或完善食物库营养信息。")
                meal_calories = max(0.0, total["protein"] * 4 + total["carbs"] * 4 + total["fat"] * 9)

            daily_calories = float(targets.get("calories") or 0)
            meal_cal_ratio = meal_calories / daily_calories if daily_calories else 0
            if daily_calories:
                tips.append(
                    f"本次餐食约 {round(meal_calories)} kcal，占您全天目标 {daily_calories} kcal 的 {round(meal_cal_ratio * 100)}%。"
                )

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
                top_sodium = sorted(item_summaries, key=lambda item: item["sodium"], reverse=True)[:2]
                top_sodium_names = [f"{item['name_zh']}({round(item['sodium'])}mg)" for item in top_sodium if item["sodium"] > 0]
                if top_sodium_names:
                    tips.append(f"本次钠主要来源：{'、'.join(top_sodium_names)}。")

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
        except Exception as exc:
            logger.error(f"Failed to generate record recommendation: {str(exc)}")
            raise CustomException(message=f"生成饮食建议失败: {str(exc)}", code=500)


food_recognition_service = FoodRecognitionService()
