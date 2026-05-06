from typing import Dict, List, Optional

from fastapi import UploadFile

from app.schemas.food import (
    FoodCategoryCreate,
    FoodCategoryUpdate,
    NutritionCreate,
    RecognitionResponse,
)
from app.services.food_catalog_service import food_catalog_service
from app.services.food_recognition_service import food_recognition_service


class FoodController:
    """食物领域门面，统一对外暴露识别、推荐与食物库能力。"""

    @staticmethod
    async def recognize_food(file: UploadFile, user_id: int) -> RecognitionResponse:
        return await food_recognition_service.recognize_food(file=file, user_id=user_id)

    @staticmethod
    async def delete_record(record_id: int, user_id: int) -> bool:
        return await food_recognition_service.delete_record(record_id=record_id, user_id=user_id)

    @staticmethod
    async def delete_records(record_ids: List[int], user_id: int) -> int:
        return await food_recognition_service.delete_records(record_ids=record_ids, user_id=user_id)

    @staticmethod
    async def get_history(user_id: int, page: int = 1, page_size: int = 10) -> Dict:
        return await food_recognition_service.get_history(user_id=user_id, page=page, page_size=page_size)

    @staticmethod
    async def get_record_detail(record_id: int, user_id: int) -> RecognitionResponse:
        return await food_recognition_service.get_record_detail(record_id=record_id, user_id=user_id)

    @staticmethod
    async def get_service_status() -> Dict:
        return await food_recognition_service.get_service_status()

    @staticmethod
    async def get_nutrition_recommendation(user_id: int, height: int, weight: float, gender: int, age: int) -> Dict:
        return await food_recognition_service.get_nutrition_recommendation(
            user_id=user_id,
            height=height,
            weight=weight,
            gender=gender,
            age=age,
        )

    @staticmethod
    async def generate_record_recommendation(record_id: int, user_id: int) -> Dict:
        return await food_recognition_service.generate_record_recommendation(record_id=record_id, user_id=user_id)

    @staticmethod
    async def get_food_categories(page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict:
        return await food_catalog_service.get_food_categories(page=page, page_size=page_size, search=search)

    @staticmethod
    async def create_food_category(category_in: FoodCategoryCreate) -> Dict:
        return await food_catalog_service.create_food_category(category_in=category_in)

    @staticmethod
    async def update_food_category(category_id: int, category_in: FoodCategoryUpdate) -> Dict:
        return await food_catalog_service.update_food_category(category_id=category_id, category_in=category_in)

    @staticmethod
    async def add_nutrition_info(nutrition_in: NutritionCreate) -> Dict:
        return await food_catalog_service.add_nutrition_info(nutrition_in=nutrition_in)

    @staticmethod
    async def get_food_category_detail(category_id: int) -> Dict:
        return await food_catalog_service.get_food_category_detail(category_id=category_id)

    @staticmethod
    async def delete_food_category(category_id: int) -> bool:
        return await food_catalog_service.delete_food_category(category_id=category_id)

    @staticmethod
    async def save_food_image(file: UploadFile) -> str:
        return await food_catalog_service.save_food_image(file=file)

    @staticmethod
    async def get_next_food_code() -> int:
        return await food_catalog_service.get_next_food_code()

    @staticmethod
    async def create_food_category_with_file(
        name: str,
        code: Optional[int] = None,
        food_type: Optional[str] = None,
        description: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        nutrition_data: Optional[Dict] = None,
    ) -> Dict:
        return await food_catalog_service.create_food_category_with_file(
            name=name,
            code=code,
            food_type=food_type,
            description=description,
            image_file=image_file,
            nutrition_data=nutrition_data,
        )

    @staticmethod
    async def update_food_category_with_file(
        category_id: int,
        name: Optional[str] = None,
        food_type: Optional[str] = None,
        description: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        image_url: Optional[str] = None,
        nutrition_data: Optional[Dict] = None,
    ) -> Dict:
        return await food_catalog_service.update_food_category_with_file(
            category_id=category_id,
            name=name,
            food_type=food_type,
            description=description,
            image_file=image_file,
            image_url=image_url,
            nutrition_data=nutrition_data,
        )
