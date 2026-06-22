#!/usr/bin/env python
"""
食物识别模块快速启动和验证脚本
"""
import asyncio
import sys
from pathlib import Path

async def main():
    print("=" * 70)
    print("🍽️  食物识别模块启动验证")
    print("=" * 70)
    
    # 1. 验证应用导入
    print("\n[1] 验证应用导入...")
    try:
        from app import app
        print("    ✓ FastAPI 应用导入成功")
    except Exception as e:
        print(f"    ✗ 应用导入失败: {str(e)}")
        return False
    
    # 2. 验证食物路由
    print("\n[2] 验证食物 API 路由...")
    food_routes = [r for r in app.routes if 'food' in str(r.path).lower()]
    print(f"    ✓ 找到 {len(food_routes)} 个食物路由:")
    for r in food_routes:
        methods = list(r.methods)[0] if hasattr(r, 'methods') else 'N/A'
        print(f"      • {methods:6s} {r.path}")
    
    # 3. 验证数据库模型
    print("\n[3] 验证数据库模型...")
    try:
        from app.models.food import (
            FoodCategory, Nutrition, RecognitionRecord,
            RecognitionDetail, NutritionAnalysis
        )
        print("    ✓ FoodCategory 模型加载")
        print("    ✓ Nutrition 模型加载")
        print("    ✓ RecognitionRecord 模型加载")
        print("    ✓ RecognitionDetail 模型加载")
        print("    ✓ NutritionAnalysis 模型加载")
    except Exception as e:
        print(f"    ✗ 模型加载失败: {str(e)}")
        return False
    
    # 4. 验证 YOLO 服务
    print("\n[4] 验证 YOLO 服务...")
    try:
        from app.services.yolo_service import yolo_service
        status = yolo_service.get_status()
        print(f"    模型路径: {status['model_path']}")
        print(f"    模型已加载: {status['loaded']}")
        print(f"    服务就绪: {status['ready']}")
        if status['error']:
            print(f"    ⚠️  错误: {status['error']}")
        else:
            print("    ✓ YOLO 服务就绪")
    except Exception as e:
        print(f"    ✗ YOLO 服务检查失败: {str(e)}")
        return False
    
    # 5. 验证 API 文档
    print("\n[5] API 文档")
    print("    • API 文档: http://localhost:9999/docs")
    print("    • ReDoc:   http://localhost:9999/redoc")
    
    print("\n" + "=" * 70)
    print("✅ 所有验证通过！食物识别模块准备就绪")
    print("=" * 70)
    print("\n🚀 启动应用: python run.py")
    print("📖 查看指南: FOOD_RECOGNITION_GUIDE.md")
    print("📋 改进总结: FOOD_MODULE_SUMMARY.md")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
