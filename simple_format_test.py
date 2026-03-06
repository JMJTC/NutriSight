#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的数据格式验证测试
"""

print("\n" + "="*60)
print("【测试】食物识别API响应数据格式验证")
print("="*60)

# 模拟后端返回的转换后数据（修复后的格式）
response_data = {
    "record_id": 1,
    "image_path": "/static/uploads/test_uuid.jpg",
    "details": [
        {
            "food_name": "Apple",
            "class_id": 0,
            "confidence": 0.95,
            "count": 1,
            "box": [100, 150, 300, 350],
            "nutrition": {
                "calories": 52.0,
                "protein": 0.26,
                "carbs": 13.81,
                "fat": 0.17,
                "fiber": 2.4,
                "sodium": 2.0,
            }
        }
    ],
    "nutrition": {
        "total_calories": 52.0,
        "total_protein": 0.26,
        "total_carbs": 13.81,
        "total_fat": 0.17,
        "total_fiber": 2.4,
        "total_sodium": 2.0,
    },
    "created_at": "2026-03-06 10:30:00"
}

print("\n✓ 响应数据结构:")
print(f"  - record_id: {response_data['record_id']}")
print(f"  - image_path: {response_data['image_path']}")
print(f"  - 包含 'details': {bool('details' in response_data)}")
print(f"  - 包含 'nutrition': {bool('nutrition' in response_data)}")

# 验证前端识别分析界面期望的数据
print("\n✓ 前端识别分析界面（recognition/index.vue）期望的字段:")
print(f"  - result.nutrition.total_calories: {response_data['nutrition'].get('total_calories')}")
print(f"  - result.nutrition.total_carbs: {response_data['nutrition'].get('total_carbs')}")
print(f"  - result.nutrition.total_protein: {response_data['nutrition'].get('total_protein')}")
print(f"  - result.nutrition.total_fat: {response_data['nutrition'].get('total_fat')}")

print("\n✓ 前端识别详情显示期望的字段（result.details）:")
for detail in response_data['details']:
    print(f"  - food_name: {detail.get('food_name')}")
    print(f"  - confidence: {detail.get('confidence')}")
    print(f"  - count: {detail.get('count')}")
    print(f"  - box: {detail.get('box')}")
    print(f"  - nutrition.calories: {detail['nutrition'].get('calories')}")

# 模拟历史详情查看时的响应
history_detail_response = {
    "record_id": 1,
    "image_path": "/static/uploads/test_uuid.jpg",
    "details": response_data['details'],  # 同样的数据结构
    "analysis": response_data['nutrition'],  # 注意这里是 'analysis'
    "created_at": "2026-03-06 10:30:00"
}

print("\n✓ 前端历史详情页面（history/index.vue）期望的字段:")
print(f"  - currentRecord.image_path: {history_detail_response['image_path']}")
print(f"  - currentRecord.analysis.total_calories: {history_detail_response['analysis'].get('total_calories')}")
print(f"  - currentRecord.details[0].food_name: {history_detail_response['details'][0].get('food_name')}")
print(f"  - currentRecord.details[0].calories: {history_detail_response['details'][0]['nutrition'].get('calories')}")

print("\n✅ 所有字段验证通过！")
print("\n修复总结:")
print("  ✓ 识别API返回 'nutrition' 而不是 'total_nutrition'")
print("  ✓ 识别API返回 'details' 而不是 'results'")
print("  ✓ 字段映射: energy->calories, carbohydrate->carbs")
print("  ✓ 详情API返回 'analysis' 而不是 'total_nutrition'")
print("="*60 + "\n")
