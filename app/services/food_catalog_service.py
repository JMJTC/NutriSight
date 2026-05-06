import os
import shutil
import uuid
from typing import Dict, Optional

from fastapi import UploadFile
from tortoise.expressions import Q

from app.core.exceptions import CustomException
from app.log import logger
from app.models.food import FoodCategory, Nutrition
from app.schemas.food import FoodCategoryCreate, FoodCategoryUpdate, NutritionCreate
from app.settings.config import settings


class FoodCatalogService:
    """食物类别、营养信息与示例图片维护服务。"""

    async def get_food_categories(self, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict:
        """获取食物类别列表。"""
        try:
            query = Q()
            if search:
                query &= Q(name__contains=search)

            offset = (page - 1) * page_size
            categories = await FoodCategory.filter(query).offset(offset).limit(page_size).order_by("code")
            count = await FoodCategory.filter(query).count()

            data = []
            for category in categories:
                category_dict = {
                    "id": category.id,
                    "name": category.name,
                    "chinese_name": category.chinese_name,
                    "code": category.code,
                    "food_type": category.food_type,
                    "description": category.description,
                    "image_url": category.image_url,
                }
                nutrition = await Nutrition.get_or_none(food=category)
                if nutrition:
                    category_dict["nutrition"] = {
                        "energy": nutrition.energy,
                        "protein": nutrition.protein,
                        "fat": nutrition.fat,
                        "carbohydrate": nutrition.carbohydrate,
                        "fiber": nutrition.fiber,
                        "sodium": nutrition.sodium,
                    }
                data.append(category_dict)

            return {"total": count, "items": data}
        except Exception as exc:
            logger.error(f"Failed to get categories: {str(exc)}")
            raise CustomException(message=f"获取食物类别失败: {str(exc)}", code=500)

    async def create_food_category(self, category_in: FoodCategoryCreate) -> Dict:
        """创建新的食物类别。"""
        try:
            existing = await FoodCategory.get_or_none(code=category_in.code)
            if existing:
                raise CustomException(message=f"YOLO 类别 ID {category_in.code} 已存在", code=400)

            existing_name = await FoodCategory.get_or_none(name=category_in.name)
            if existing_name:
                raise CustomException(message=f"食物名称 {category_in.name} 已存在", code=400)

            category = await FoodCategory.create(
                name=category_in.name,
                chinese_name=category_in.chinese_name,
                code=category_in.code,
                food_type=category_in.food_type,
                description=category_in.description,
                image_url=category_in.image_url,
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
        except Exception as exc:
            logger.error(f"Failed to create category: {str(exc)}")
            raise CustomException(message=f"创建食物类别失败: {str(exc)}", code=500)

    async def update_food_category(self, category_id: int, category_in: FoodCategoryUpdate) -> Dict:
        """更新食物类别信息。"""
        try:
            category = await FoodCategory.get_or_none(id=category_id)
            if not category:
                raise CustomException(message=f"食物类别 {category_id} 不存在", code=404)

            if category_in.name and category_in.name != category.name:
                existing = await FoodCategory.get_or_none(name=category_in.name)
                if existing:
                    raise CustomException(message=f"食物名称 {category_in.name} 已存在", code=400)

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
        except Exception as exc:
            logger.error(f"Failed to update category: {str(exc)}")
            raise CustomException(message=f"更新食物类别失败: {str(exc)}", code=500)

    async def add_nutrition_info(self, nutrition_in: NutritionCreate) -> Dict:
        """为食物类别添加或更新营养信息。"""
        try:
            food = await FoodCategory.get_or_none(id=nutrition_in.food_id)
            if not food:
                raise CustomException(message=f"食物类别 {nutrition_in.food_id} 不存在", code=404)

            nutrition = await Nutrition.get_or_none(food=food)
            if nutrition:
                nutrition.energy = nutrition_in.energy
                nutrition.protein = nutrition_in.protein
                nutrition.fat = nutrition_in.fat
                nutrition.carbohydrate = nutrition_in.carbohydrate
                nutrition.fiber = nutrition_in.fiber
                nutrition.sodium = nutrition_in.sodium
                await nutrition.save()
                logger.info(f"Nutrition info for food {nutrition_in.food_id} updated")
            else:
                nutrition = await Nutrition.create(
                    food=food,
                    energy=nutrition_in.energy,
                    protein=nutrition_in.protein,
                    fat=nutrition_in.fat,
                    carbohydrate=nutrition_in.carbohydrate,
                    fiber=nutrition_in.fiber,
                    sodium=nutrition_in.sodium,
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
        except Exception as exc:
            logger.error(f"Failed to add nutrition info: {str(exc)}")
            raise CustomException(message=f"保存营养信息失败: {str(exc)}", code=500)

    async def get_food_category_detail(self, category_id: int) -> Dict:
        """获取单个食物类别的详细信息。"""
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
        except Exception as exc:
            logger.error(f"Failed to get category detail: {str(exc)}")
            raise CustomException(message=f"获取食物类别详情失败: {str(exc)}", code=500)

    async def delete_food_category(self, category_id: int) -> bool:
        """删除食物类别及其关联营养信息。"""
        try:
            category = await FoodCategory.get_or_none(id=category_id)
            if not category:
                raise CustomException(message=f"食物类别 {category_id} 不存在", code=404)

            nutrition = await Nutrition.get_or_none(food=category)
            if nutrition:
                await nutrition.delete()
                logger.info(f"Deleted nutrition info for food category {category_id}")

            await category.delete()
            logger.info(f"Food category {category_id} deleted")
            return True
        except CustomException:
            raise
        except Exception as exc:
            logger.error(f"Failed to delete category: {str(exc)}")
            raise CustomException(message=f"删除食物类别失败: {str(exc)}", code=500)

    async def save_food_image(self, file: UploadFile) -> str:
        """保存食物示例图片。"""
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
        except Exception as exc:
            logger.error(f"Failed to save food image: {str(exc)}")
            raise CustomException(message=f"图片保存失败: {str(exc)}", code=500)

    async def get_next_food_code(self) -> int:
        """获取下一个可用的 YOLO 类别 ID。"""
        try:
            all_foods = await FoodCategory.all()
            if all_foods:
                max_code = max([food.code for food in all_foods if isinstance(food.code, int)])
                return max_code + 1
            return 0
        except Exception as exc:
            logger.error(f"Error getting next food code: {str(exc)}")
            return 0

    async def create_food_category_with_file(
        self,
        name: str,
        code: Optional[int] = None,
        food_type: Optional[str] = None,
        description: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        nutrition_data: Optional[Dict] = None,
    ) -> Dict:
        """创建食物类别，支持图片上传和营养信息。"""
        try:
            existing_name = await FoodCategory.get_or_none(name=name)
            if existing_name:
                raise CustomException(message=f"食物名称 {name} 已存在", code=400)

            if code is None or code == "":
                code = await self.get_next_food_code()
                logger.info(f"Auto-generated code for food {name}: {code}")
            else:
                existing_code = await FoodCategory.get_or_none(code=code)
                if existing_code:
                    raise CustomException(message=f"YOLO 类别 ID {code} 已存在", code=400)

            image_url = None
            if image_file:
                image_url = await self.save_food_image(image_file)

            category = await FoodCategory.create(
                name=name,
                code=code,
                food_type=food_type,
                description=description,
                image_url=image_url,
            )

            if nutrition_data:
                await Nutrition.create(
                    food=category,
                    energy=float(nutrition_data.get("energy", 0)),
                    protein=float(nutrition_data.get("protein", 0)),
                    fat=float(nutrition_data.get("fat", 0)),
                    carbohydrate=float(nutrition_data.get("carbohydrate", 0)),
                    fiber=float(nutrition_data.get("fiber", 0)),
                    sodium=float(nutrition_data.get("sodium", 0)),
                )
                logger.info(f"Nutrition info created for food category {category.id}")

            logger.info(f"Food category {category.id} created with image: {name}")
            return await self.get_food_category_detail(category.id)
        except CustomException:
            raise
        except Exception as exc:
            logger.error(f"Failed to create category with file: {str(exc)}")
            raise CustomException(message=f"创建食物类别失败: {str(exc)}", code=500)

    async def update_food_category_with_file(
        self,
        category_id: int,
        name: Optional[str] = None,
        food_type: Optional[str] = None,
        description: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        image_url: Optional[str] = None,
        nutrition_data: Optional[Dict] = None,
    ) -> Dict:
        """更新食物类别，支持图片上传和营养信息更新。"""
        try:
            category = await FoodCategory.get_or_none(id=category_id)
            if not category:
                raise CustomException(message=f"食物类别 {category_id} 不存在", code=404)

            if name and name != category.name:
                existing = await FoodCategory.get_or_none(name=name)
                if existing:
                    raise CustomException(message=f"食物名称 {name} 已存在", code=400)
                category.name = name

            if food_type is not None:
                category.food_type = food_type
            if description is not None:
                category.description = description

            if image_file:
                image_url = await self.save_food_image(image_file)
            if image_url is not None:
                category.image_url = image_url

            await category.save()

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
                    await Nutrition.create(
                        food=category,
                        energy=float(nutrition_data.get("energy", 0)),
                        protein=float(nutrition_data.get("protein", 0)),
                        fat=float(nutrition_data.get("fat", 0)),
                        carbohydrate=float(nutrition_data.get("carbohydrate", 0)),
                        fiber=float(nutrition_data.get("fiber", 0)),
                        sodium=float(nutrition_data.get("sodium", 0)),
                    )
                    logger.info(f"Nutrition info created for food {category_id}")

            logger.info(f"Food category {category_id} updated")
            return await self.get_food_category_detail(category.id)
        except CustomException:
            raise
        except Exception as exc:
            logger.error(f"Failed to update category with file: {str(exc)}")
            raise CustomException(message=f"更新食物类别失败: {str(exc)}", code=500)


food_catalog_service = FoodCatalogService()
