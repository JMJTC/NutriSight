"""
集成食物识别映射数据初始化脚本

该脚本根据 integrated_food_mapping.json 初始化数据库中的食物类别（FoodCategory）和营养信息（Nutrition）。
初始化前会清空相关的表。

运行方式：
uv run python app/scripts/init_integrated_food_data.py
"""

import asyncio
import json
import os
import sys

# 将项目根目录添加到 python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tortoise import Tortoise
from app.models.food import FoodCategory, Nutrition, RecognitionDetail, RecognitionRecord, NutritionAnalysis
from app.settings.config import settings
from app.log import logger

# 数据文件路径
MAPPING_FILE = os.path.join(settings.BASE_DIR, "deploy", "integrated_food_mapping.json")

async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(config=settings.TORTOISE_ORM)
    logger.info("Database connection initialized.")

async def clear_existing_data():
    """清空相关表的数据"""
    logger.info("Clearing existing food-related data...")
    try:
        # 由于外键约束，需要按顺序删除
        # 1. 删除识别记录相关的详情和分析
        await NutritionAnalysis.all().delete()
        await RecognitionDetail.all().delete()
        await RecognitionRecord.all().delete()
        
        # 2. 删除营养信息
        await Nutrition.all().delete()
        
        # 3. 删除食物类别
        await FoodCategory.all().delete()
        
        logger.info("✓ All existing food-related data cleared.")
    except Exception as e:
        logger.error(f"✗ Failed to clear existing data: {str(e)}")
        raise e

async def load_and_insert_data():
    """加载 JSON 并插入数据库"""
    if not os.path.exists(MAPPING_FILE):
        logger.error(f"Mapping file not found: {MAPPING_FILE}")
        return

    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)

    logger.info(f"Loaded {len(mapping_data)} food items from mapping file.")
    
    created_count = 0
    error_count = 0

    for key, item in mapping_data.items():
        try:
            # 检查 code 是否已存在，如果存在则跳过（处理 JSON 中重复的 code）
            existing = await FoodCategory.get_or_none(code=item["code"])
            if existing:
                logger.warning(f"Skipping duplicate code {item['code']} for food: {item['english_name']} (already exists as {existing.name})")
                continue

            # 创建食物类别
            category = await FoodCategory.create(
                name=item["english_name"],
                chinese_name=item["chinese_name"],
                code=item["code"],
                food_type=item["food_type"],
                description=item["description"],
                image_url=item["image_url"]
            )
            
            # 创建营养信息
            nutrition_data = item.get("nutrition", {})
            await Nutrition.create(
                food=category,
                energy=nutrition_data.get("energy", 0.0),
                protein=nutrition_data.get("protein", 0.0),
                fat=nutrition_data.get("fat", 0.0),
                carbohydrate=nutrition_data.get("carbohydrate", 0.0),
                fiber=nutrition_data.get("fiber", 0.0),
                sodium=nutrition_data.get("sodium", 0.0)
            )
            
            created_count += 1
            if created_count % 20 == 0:
                logger.info(f"Progress: {created_count}/{len(mapping_data)} items created...")
                
        except Exception as e:
            logger.error(f"Failed to insert item {item.get('english_name')}: {str(e)}")
            error_count += 1

    logger.info(f"✓ Data insertion complete. Total: {created_count}, Errors: {error_count}")

async def main():
    try:
        await init_db()
        await clear_existing_data()
        await load_and_insert_data()
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
