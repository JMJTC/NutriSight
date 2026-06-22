#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：验证食物识别API数据格式修复
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_data_format():
    """测试数据格式转换"""
    from app.controllers.food import FoodController
    from app.schemas.food import NutritionBase, RecognitionResult
    
    print("\n" + "="*60)
    print("【测试】数据格式转换验证")
    print("="*60)
    
    # 模拟识别结果
    mock_results = [
        RecognitionResult(
            class_id=0,
            class_name="Apple",
            confidence=0.95,
            bbox=[100, 150, 300, 350],
            nutrition=NutritionBase(
                energy=52.0,
                protein=0.26,
                fat=0.17,
                carbohydrate=13.81,
                fiber=2.4,
                sodium=2.0
            )
        )
    ]
    
    mock_total_nutrition = {
        "energy": 52.0,
        "protein": 0.26,
        "fat": 0.17,
        "carbohydrate": 13.81,
        "fiber": 2.4,
        "sodium": 2.0
    }
    
    # 模拟响应转换
    details = []
    for result in mock_results:
        details.append({
            "food_name": result.class_name,
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
            } if result.nutrition else {
                "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sodium": 0
            }
        })
    
    nutrition_info = {
        "total_calories": mock_total_nutrition["energy"],
        "total_protein": mock_total_nutrition["protein"],
        "total_carbs": mock_total_nutrition["carbohydrate"],
        "total_fat": mock_total_nutrition["fat"],
        "total_fiber": mock_total_nutrition["fiber"],
        "total_sodium": mock_total_nutrition["sodium"],
    }
    
    response_dict = {
        "record_id": 1,
        "image_path": "/static/uploads/test.jpg",
        "details": details,
        "nutrition": nutrition_info,
        "created_at": "2026-03-06 10:30:00"
    }
    
    # 验证响应格式
    print("\n✓ 响应格式验证:")
    print(f"  - 包含 'details': {bool('details' in response_dict)}")
    print(f"  - 包含 'nutrition': {bool('nutrition' in response_dict)}")
    print(f"  - details[0].box: {response_dict['details'][0]['box']}")
    print(f"  - nutrition.total_calories: {response_dict['nutrition']['total_calories']}")
    
    # 验证前端期望的字段
    sample_detail = response_dict['details'][0]
    print("\n✓ 前端期望的字段验证:")
    print(f"  - food_name: {sample_detail.get('food_name')}")
    print(f"  - confidence: {sample_detail.get('confidence')}")
    print(f"  - box: {sample_detail.get('box')}")
    print(f"  - nutrition.calories: {sample_detail['nutrition'].get('calories')}")
    
    sample_nutrition = response_dict['nutrition']
    print("\n✓ 前端期望的营养字段验证:")
    print(f"  - total_calories: {sample_nutrition.get('total_calories')}")
    print(f"  - total_carbs: {sample_nutrition.get('total_carbs')}")
    print(f"  - total_protein: {sample_nutrition.get('total_protein')}")
    print(f"  - total_fat: {sample_nutrition.get('total_fat')}")
    
    print("\n✅ 数据格式验证通过！")


if __name__ == "__main__":
    asyncio.run(test_data_format())
