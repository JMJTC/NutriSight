"""
根据 integrated_food_mapping.json 初始化数据库数据脚本

这个脚本读取 integrated_food_mapping.json 文件，清空 FoodCategory 和 Nutrition 表，
然后插入新的食物数据。

运行方式：python -c "from app.scripts.init_from_mapping import init_from_mapping; import asyncio; asyncio.run(init_from_mapping())"
"""

import asyncio
import json
import os
from pathlib import Path

from tortoise import Tortoise

from app.models.food import FoodCategory, Nutrition
from app.log import logger
from app.settings.config import settings


async def init_from_mapping():
    """从 integrated_food_mapping.json 初始化食物数据"""
    try:
        # 初始化 Tortoise
        await Tortoise.init(config=settings.TORTOISE_ORM)
        
        # 获取文件路径
        base_dir = Path(__file__).parent.parent.parent
        mapping_file = base_dir / "deploy" / "integrated_food_mapping.json"
        
        if not mapping_file.exists():
            logger.error(f"Mapping file not found: {mapping_file}")
            return {"error": "Mapping file not found"}
        
        # 读取 JSON 数据
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} food items from mapping file")
        
        # 清空相关表
        logger.info("Clearing existing food data...")
        await Nutrition.all().delete()
        await FoodCategory.all().delete()
        logger.info("Tables cleared")
        
        created_count = 0
        skipped_count = 0
        
        # 插入数据
        for key, item in data.items():
            try:
                # 检查是否已存在相同 code 的记录
                existing = await FoodCategory.filter(code=item['code']).first()
                if existing:
                    logger.warning(f"Food with code {item['code']} already exists, skipping")
                    skipped_count += 1
                    continue
                
                # 创建 FoodCategory
                food_category = await FoodCategory.create(
                    name=item['english_name'],
                    chinese_name=item['chinese_name'],
                    code=item['code'],
                    food_type=item['food_type'],
                    description=item['description'],
                    image_url=item['image_url']
                )
                
                # 创建 Nutrition
                await Nutrition.create(
                    food=food_category,
                    energy=item['nutrition']['energy'],
                    protein=item['nutrition']['protein'],
                    fat=item['nutrition']['fat'],
                    carbohydrate=item['nutrition']['carbohydrate'],
                    fiber=item['nutrition']['fiber'],
                    sodium=item['nutrition']['sodium']
                )
                
                created_count += 1
                logger.info(f"Created food: {item['chinese_name']} ({item['english_name']})")
                
            except Exception as e:
                logger.error(f"Error creating food {key}: {str(e)}")
                skipped_count += 1
                continue
        
        logger.info(f"Initialization complete. Created: {created_count}, Skipped: {skipped_count}")
        return {"created": created_count, "skipped": skipped_count}
        
    except Exception as e:
        logger.error(f"Failed to initialize from mapping: {str(e)}")
        return {"error": str(e)}
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(init_from_mapping())