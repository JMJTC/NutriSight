import asyncio
import os
import sys
sys.path.append('.')

from app.services.yolo_service import yolo_service
from app.controllers.food import FoodController
from app.models.food import RecognitionRecord

async def test_recognition():
    """测试识别功能"""
    print("Testing food recognition...")

    # 检查YOLO服务
    if not yolo_service.is_ready():
        print("YOLO service not ready")
        return

    print("YOLO service is ready")

    # 创建一个测试图片路径（使用现有图片）
    uploads_dir = "deploy/static/uploads"
    if os.path.exists(uploads_dir):
        files = os.listdir(uploads_dir)
        if files:
            test_image_path = os.path.join(uploads_dir, files[0])
            print(f"Using existing image: {test_image_path}")
        else:
            print("No images found in uploads directory")
            return
    else:
        print(f"Uploads directory not found: {uploads_dir}")
        return

    print(f"Testing with image: {test_image_path}")

    # 测试YOLO预测
    try:
        predictions, annotated_path = yolo_service.predict_with_annotation(test_image_path, conf=0.1)  # 降低置信度阈值
        print(f"Predictions: {len(predictions)} items")
        print(f"Annotated image path: {annotated_path}")

        if predictions:
            print("Sample prediction:", predictions[0])

        if annotated_path:
            full_path = f"deploy/static{annotated_path}"
            if os.path.exists(full_path):
                print("Annotated image created successfully")
            else:
                print(f"Annotated image not found at: {full_path}")
        else:
            print("Annotated image not created")

    except Exception as e:
        print(f"Error during prediction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recognition())