"""
食物识别模块健康检查脚本
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def health_check():
    """执行健康检查"""
    print("=" * 60)
    print("食物识别模块健康检查")
    print("=" * 60)
    
    # 检查 1: YOLO 模型文件
    print("\n[1] 检查 YOLO 模型文件...")
    from app.settings.config import settings
    
    best_model = Path(settings.BASE_DIR) / "weights" / "best.pt"
    last_model = Path(settings.BASE_DIR) / "weights" / "last.pt"
    
    if best_model.exists():
        size_mb = best_model.stat().st_size / (1024 * 1024)
        print(f"    ✓ best.pt 存在 ({size_mb:.2f} MB)")
    else:
        print(f"    ✗ best.pt 不存在 ({best_model})")
    
    if last_model.exists():
        size_mb = last_model.stat().st_size / (1024 * 1024)
        print(f"    ✓ last.pt 存在 ({size_mb:.2f} MB)")
    else:
        print(f"    ✗ last.pt 不存在 ({last_model})")
    
    # 检查 2: YOLO 服务初始化
    print("\n[2] 检查 YOLO 服务初始化...")
    try:
        from app.services.yolo_service import yolo_service
        status = yolo_service.get_status()
        print(f"    YOLO 服务状态: {status['status']}")
        print(f"    模型加载: {status['loaded']}")
        if status['error']:
            print(f"    错误: {status['error']}")
    except Exception as e:
        print(f"    ✗ YOLO 服务初始化失败: {str(e)}")
        return
    
    # 检查 3: 数据库模型
    print("\n[3] 检查数据库模型...")
    try:
        from app.models.food import FoodCategory, Nutrition, RecognitionRecord
        print(f"    ✓ FoodCategory 模型已加载")
        print(f"    ✓ Nutrition 模型已加载")
        print(f"    ✓ RecognitionRecord 模型已加载")
    except Exception as e:
        print(f"    ✗ 数据库模型加载失败: {str(e)}")
        return
    
    # 检查 4: API 路由
    print("\n[4] 检查 API 路由...")
    try:
        from app.api.v1.food.food import food_router
        routes = [route.path for route in food_router.routes]
        print(f"    ✓ 食物 API 路由已加载")
        print(f"    路由数: {len(routes)}")
        for route in routes:
            print(f"      - {route}")
    except Exception as e:
        print(f"    ✗ API 路由加载失败: {str(e)}")
        return
    
    # 检查 5: 数据库连接
    print("\n[5] 检查数据库连接...")
    try:
        from tortoise import Tortoise
        if Tortoise.is_initialized():
            print(f"    ✓ 数据库已初始化")
            cat_count = await FoodCategory.all().count()
            nutrition_count = await Nutrition.all().count()
            record_count = await RecognitionRecord.all().count()
            print(f"      - 食物类别数: {cat_count}")
            print(f"      - 营养信息数: {nutrition_count}")
            print(f"      - 识别记录数: {record_count}")
        else:
            print(f"    ℹ 数据库尚未初始化（应用启动时连接）")
    except Exception as e:
        print(f"    ℹ 数据库连接检查: {str(e)}")
    
    print("\n" + "=" * 60)
    print("健康检查完成 ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(health_check())
    except Exception as e:
        print(f"\n❌ 健康检查失败: {str(e)}")
        sys.exit(1)
