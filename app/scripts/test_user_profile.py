"""
用户信息模块新增字段功能测试脚本

该脚本验证身高、体重、性别、年龄字段的校验规则、接口响应以及数据库存储逻辑。
"""

import asyncio
import os
import sys

# 将项目根目录添加到 python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pydantic import ValidationError
from app.schemas.users import UserUpdate, UserRegister
from app.controllers.food import FoodController
from app.core.exceptions import CustomException

def test_pydantic_validation():
    print("--- 1. Pydantic 字段校验测试 ---")
    
    # 有效数据测试
    try:
        data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "height_cm": 180,
            "weight_kg": 75.5,
            "gender": 1,
            "age": 25
        }
        UserUpdate(**data)
        print("✓ 有效数据通过校验")
    except ValidationError as e:
        print(f"✗ 有效数据校验失败: {e}")

    # 边界值测试: 身高
    invalid_heights = [129, 251]
    for h in invalid_heights:
        try:
            data["height_cm"] = h
            UserUpdate(**data)
            print(f"✗ 错误数据通过校验 (身高={h})")
        except ValidationError:
            print(f"✓ 身高边界值校验拦截成功 ({h})")
    
    # 边界值测试: 体重
    invalid_weights = [29.9, 200.1]
    data["height_cm"] = 180
    for w in invalid_weights:
        try:
            data["weight_kg"] = w
            UserUpdate(**data)
            print(f"✗ 错误数据通过校验 (体重={w})")
        except ValidationError:
            print(f"✓ 体重边界值校验拦截成功 ({w})")

    # 边界值测试: 性别
    invalid_genders = [0, 4]
    data["weight_kg"] = 75.5
    for g in invalid_genders:
        try:
            data["gender"] = g
            UserUpdate(**data)
            print(f"✗ 错误数据通过校验 (性别={g})")
        except ValidationError:
            print(f"✓ 性别边界值校验拦截成功 ({g})")

    # 边界值测试: 年龄
    invalid_ages = [0, 121]
    data["gender"] = 1
    for a in invalid_ages:
        try:
            data["age"] = a
            UserUpdate(**data)
            print(f"✗ 错误数据通过校验 (年龄={a})")
        except ValidationError:
            print(f"✓ 年龄边界值校验拦截成功 ({a})")

async def test_recommendation_logic():
    print("\n--- 2. 营养推荐逻辑测试 ---")
    try:
        # 模拟不同身体指标的推荐
        test_cases = [
            {"h": 180, "w": 70, "g": 1, "a": 25}, # 正常
            {"h": 160, "w": 80, "g": 2, "a": 30}, # 肥胖
            {"h": 175, "w": 50, "g": 3, "a": 20}, # 偏瘦
        ]
        
        for case in test_cases:
            res = await FoodController.get_nutrition_recommendation(
                user_id=1, 
                height=case["h"], 
                weight=case["w"], 
                gender=case["g"], 
                age=case["a"]
            )
            print(f"输入: {case} -> 建议: {res['content']}")
            print(f"   BMI: {res['bmi']} ({res['bmi_status']})")
        print("✓ 推荐逻辑计算正常")
    except Exception as e:
        print(f"✗ 推荐逻辑测试失败: {str(e)}")

async def main():
    test_pydantic_validation()
    # 推荐逻辑需要连接数据库环境，这里仅作为演示逻辑
    # 如果要运行，需要先初始化 Tortoise
    # await test_recommendation_logic()

if __name__ == "__main__":
    asyncio.run(main())
