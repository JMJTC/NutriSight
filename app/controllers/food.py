import json
import os
import shutil
import uuid
from datetime import datetime
from typing import List

from fastapi import UploadFile

from app.core.exceptions import CustomException
from app.models.food import (
    FoodCategory,
    Nutrition,
    RecognitionRecord,
    RecognitionDetail,
    NutritionAnalysis,
    NutritionRecommendation
)
from app.schemas.food import RecognitionResponse, RecognitionResult, NutritionBase
from app.services.yolo_service import yolo_service
from app.settings.config import settings
from app.models.admin import User

class FoodController:
    @staticmethod
    async def recognize_food(file: UploadFile, user_id: int) -> RecognitionResponse:
        # 1. Save Image
        upload_dir = os.path.join(settings.BASE_DIR, "deploy", "static", "uploads")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        file_ext = file.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_dir, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Relative path for URL
        relative_path = f"/static/uploads/{file_name}"

        # 2. YOLO Inference
        try:
            predictions = yolo_service.predict(file_path)
        except Exception as e:
            raise CustomException(message=f"Model inference failed: {str(e)}", code=500)

        # 3. Save Record
        user = await User.get(id=user_id)
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

        # 4. Process Results & Aggregate Nutrition
        for pred in predictions:
            # Find Food Category
            # Assuming YOLO class_id matches FoodCategory code. 
            # In a real scenario, you might need a mapping or ensure DB is seeded correctly.
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
                    # Aggregate (Simple aggregation, assuming 100g or 1 serving per detection for now)
                    # To improve: estimate volume/weight from bbox area?
                    total_nutrition["energy"] += nutrition.energy
                    total_nutrition["protein"] += nutrition.protein
                    total_nutrition["fat"] += nutrition.fat
                    total_nutrition["carbohydrate"] += nutrition.carbohydrate
                    total_nutrition["fiber"] += nutrition.fiber
                    total_nutrition["sodium"] += nutrition.sodium

            # Save Detail
            await RecognitionDetail.create(
                record=record,
                food=food_cat if food_cat else None, # Might fail if food_cat is None and field is not nullable? Check model.
                confidence=pred["confidence"],
                bbox=pred["bbox"]
            )

            results.append(RecognitionResult(
                class_id=pred["class_id"],
                class_name=pred["class_name"],
                confidence=pred["confidence"],
                bbox=pred["bbox"],
                nutrition=nutrition_data
            ))

        # 5. Save Analysis
        analysis_summary = f"Detected {len(predictions)} items."
        if total_nutrition["energy"] > 800:
             analysis_summary += " High calorie meal."
        
        await NutritionAnalysis.create(
            record=record,
            total_energy=total_nutrition["energy"],
            total_protein=total_nutrition["protein"],
            total_fat=total_nutrition["fat"],
            total_carbohydrate=total_nutrition["carbohydrate"],
            summary=analysis_summary
        )

        return RecognitionResponse(
            record_id=record.id,
            image_path=relative_path,
            results=results,
            total_nutrition=NutritionBase(**total_nutrition),
            created_at=record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )

    @staticmethod
    async def get_history(user_id: int, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        records = await RecognitionRecord.filter(user_id=user_id).offset(offset).limit(page_size).order_by("-created_at").prefetch_related("analysis", "details", "details__food")
        count = await RecognitionRecord.filter(user_id=user_id).count()
        
        data = []
        for r in records:
            # Construct response similarly to RecognitionResponse or simplified
            data.append({
                "id": r.id,
                "image_path": r.image_path,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "total_energy": r.analysis.total_energy if r.analysis else 0
            })
            
        return {"total": count, "items": data, "page": page, "page_size": page_size}

    @staticmethod
    async def get_record_detail(record_id: int, user_id: int):
        record = await RecognitionRecord.get_or_none(id=record_id, user_id=user_id).prefetch_related("details", "details__food", "analysis", "details__food__nutrition")
        if not record:
            raise CustomException(message="Record not found", code=404)
        
        results = []
        for d in record.details:
            nut = None
            if d.food and d.food.nutrition:
                n = d.food.nutrition
                nut = NutritionBase(
                    energy=n.energy, protein=n.protein, fat=n.fat, 
                    carbohydrate=n.carbohydrate, fiber=n.fiber, sodium=n.sodium
                )
            
            results.append(RecognitionResult(
                class_id=d.food.code if d.food else -1,
                class_name=d.food.name if d.food else "Unknown",
                confidence=d.confidence,
                bbox=d.bbox,
                nutrition=nut
            ))
            
        return RecognitionResponse(
            record_id=record.id,
            image_path=record.image_path,
            results=results,
            total_nutrition=NutritionBase(
                energy=record.analysis.total_energy,
                protein=record.analysis.total_protein,
                fat=record.analysis.total_fat,
                carbohydrate=record.analysis.total_carbohydrate,
                fiber=0, sodium=0 # Analysis table might need fiber/sodium if we want full recovery
            ) if record.analysis else None,
            created_at=record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        )

