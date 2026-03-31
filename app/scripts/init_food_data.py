"""
食物识别模块数据库初始化脚本

这个脚本初始化食物类别（FoodCategory）和营养信息（Nutrition）
运行方式：python -c "from app.scripts.init_food_data import init_food_data; import asyncio; asyncio.run(init_food_data())"
"""

import asyncio
from app.models.food import FoodCategory, Nutrition
from app.log import logger

# 默认食物类别和营养信息数据
DEFAULT_FOOD_DATA = [
    {
        "name": "Apple",
        "code": 0,
        "food_type": "Fruit",
        "description": "Fresh apple",
        "image_url": None,
        "nutrition": {
            "energy": 52.0,
            "protein": 0.26,
            "fat": 0.17,
            "carbohydrate": 13.81,
            "fiber": 2.4,
            "sodium": 2.0
        }
    },
    {
        "name": "Banana",
        "code": 1,
        "food_type": "Fruit",
        "description": "Fresh banana",
        "image_url": None,
        "nutrition": {
            "energy": 89.0,
            "protein": 1.09,
            "fat": 0.33,
            "carbohydrate": 23.0,
            "fiber": 2.6,
            "sodium": 2.0
        }
    },
    {
        "name": "Orange",
        "code": 2,
        "food_type": "Fruit",
        "description": "Fresh orange",
        "image_url": None,
        "nutrition": {
            "energy": 47.0,
            "protein": 0.91,
            "fat": 0.12,
            "carbohydrate": 11.75,
            "fiber": 2.4,
            "sodium": 2.0
        }
    },
    {
        "name": "Carrot",
        "code": 3,
        "food_type": "Vegetable",
        "description": "Fresh carrot",
        "image_url": None,
        "nutrition": {
            "energy": 41.0,
            "protein": 0.93,
            "fat": 0.24,
            "carbohydrate": 9.58,
            "fiber": 2.8,
            "sodium": 69.0
        }
    },
    {
        "name": "Broccoli",
        "code": 4,
        "food_type": "Vegetable",
        "description": "Fresh broccoli",
        "image_url": None,
        "nutrition": {
            "energy": 34.0,
            "protein": 2.82,
            "fat": 0.37,
            "carbohydrate": 6.64,
            "fiber": 2.4,
            "sodium": 64.0
        }
    },
    {
        "name": "Chicken Breast",
        "code": 5,
        "food_type": "Meat",
        "description": "Cooked chicken breast",
        "image_url": None,
        "nutrition": {
            "energy": 165.0,
            "protein": 31.0,
            "fat": 3.6,
            "carbohydrate": 0.0,
            "fiber": 0.0,
            "sodium": 74.0
        }
    },
    {
        "name": "Beef",
        "code": 6,
        "food_type": "Meat",
        "description": "Cooked lean beef",
        "image_url": None,
        "nutrition": {
            "energy": 250.0,
            "protein": 26.0,
            "fat": 15.0,
            "carbohydrate": 0.0,
            "fiber": 0.0,
            "sodium": 75.0
        }
    },
    {
        "name": "Salmon",
        "code": 7,
        "food_type": "Fish",
        "description": "Cooked salmon",
        "image_url": None,
        "nutrition": {
            "energy": 208.0,
            "protein": 20.0,
            "fat": 13.0,
            "carbohydrate": 0.0,
            "fiber": 0.0,
            "sodium": 75.0
        }
    },
    {
        "name": "Rice",
        "code": 8,
        "food_type": "Grain",
        "description": "Cooked white rice",
        "image_url": None,
        "nutrition": {
            "energy": 130.0,
            "protein": 2.69,
            "fat": 0.3,
            "carbohydrate": 28.0,
            "fiber": 0.4,
            "sodium": 1.0
        }
    },
    {
        "name": "Bread",
        "code": 9,
        "food_type": "Grain",
        "description": "Whole wheat bread",
        "image_url": None,
        "nutrition": {
            "energy": 265.0,
            "protein": 9.0,
            "fat": 3.3,
            "carbohydrate": 49.0,
            "fiber": 6.8,
            "sodium": 450.0
        }
    },
    {
        "name": "Egg",
        "code": 10,
        "food_type": "Protein",
        "description": "Boiled egg",
        "image_url": None,
        "nutrition": {
            "energy": 155.0,
            "protein": 13.0,
            "fat": 11.0,
            "carbohydrate": 1.1,
            "fiber": 0.0,
            "sodium": 140.0
        }
    },
    {
        "name": "Milk",
        "code": 11,
        "food_type": "Dairy",
        "description": "Whole milk",
        "image_url": None,
        "nutrition": {
            "energy": 61.0,
            "protein": 3.15,
            "fat": 3.25,
            "carbohydrate": 4.8,
            "fiber": 0.0,
            "sodium": 44.0
        }
    },
    {
        "name": "Yogurt",
        "code": 12,
        "food_type": "Dairy",
        "description": "Plain yogurt",
        "image_url": None,
        "nutrition": {
            "energy": 59.0,
            "protein": 3.5,
            "fat": 0.4,
            "carbohydrate": 3.25,
            "fiber": 0.0,
            "sodium": 46.0
        }
    },
    {
        "name": "Tomato",
        "code": 13,
        "food_type": "Vegetable",
        "description": "Fresh tomato",
        "image_url": None,
        "nutrition": {
            "energy": 18.0,
            "protein": 0.88,
            "fat": 0.2,
            "carbohydrate": 3.89,
            "fiber": 1.2,
            "sodium": 12.0
        }
    },
    {
        "name": "Lettuce",
        "code": 14,
        "food_type": "Vegetable",
        "description": "Fresh lettuce",
        "image_url": None,
        "nutrition": {
            "energy": 15.0,
            "protein": 1.35,
            "fat": 0.15,
            "carbohydrate": 2.87,
            "fiber": 1.3,
            "sodium": 5.0
        }
    },
]


async def init_food_data():
    """
    初始化食物类别和营养信息
    """
    logger.info("Starting food data initialization...")
    created_count = 0
    skipped_count = 0
    
    for item in DEFAULT_FOOD_DATA:
        try:
            # 检查是否已存在
            existing = await FoodCategory.get_or_none(code=item["code"])
            if existing:
                logger.info(f"Food category '{item['name']}' (code: {item['code']}) already exists, skipping...")
                skipped_count += 1
                continue
            
            # 创建食物类别
            category = await FoodCategory.create(
                name=item["name"],
                code=item["code"],
                food_type=item["food_type"],
                description=item["description"],
                image_url=item["image_url"]
            )
            logger.info(f"Created food category: {item['name']} (ID: {category.id}, Code: {item['code']})")
            
            # 创建营养信息
            nutrition_data = item.get("nutrition")
            if nutrition_data:
                nutrition = await Nutrition.create(
                    food=category,
                    energy=nutrition_data["energy"],
                    protein=nutrition_data["protein"],
                    fat=nutrition_data["fat"],
                    carbohydrate=nutrition_data["carbohydrate"],
                    fiber=nutrition_data["fiber"],
                    sodium=nutrition_data["sodium"]
                )
                logger.info(f"Created nutrition info for: {item['name']} (Energy: {nutrition_data['energy']} kcal/100g)")
            
            created_count += 1
        except Exception as e:
            logger.error(f"Failed to create food '{item['name']}': {str(e)}")
    
    logger.info(f"Food data initialization complete. Created: {created_count}, Skipped: {skipped_count}")
    return {"created": created_count, "skipped": skipped_count}


async def clear_food_data():
    """
    清除所有食物数据（仅用于测试）
    """
    try:
        # 删除所有营养信息
        await Nutrition.all().delete()
        # 删除所有食物类别
        await FoodCategory.all().delete()
        logger.info("Food data cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear food data: {str(e)}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        asyncio.run(clear_food_data())
    else:
        asyncio.run(init_food_data())
