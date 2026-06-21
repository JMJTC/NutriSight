#!/usr/bin/env python
import asyncio
import sys
sys.path.append('.')

from app.services.yolo_service import yolo_service
from app.controllers.food import FoodController
from app.models.admin import User

async def test_full_flow():
    """测试完整的识别流程"""
    print("Testing full recognition flow...")
    
    # Check YOLO service
    if not yolo_service.is_ready():
        print("YOLO service not ready")
        return
    
    print("✓ YOLO service is ready")
    
    # Test prediction with a real image
    test_image = "deploy/static/uploads/049ac5f6-038e-4882-a1c4-a1ee5aac85de.jpg"
    
    print(f"\nTesting prediction with: {test_image}")
    predictions, annotated_path = yolo_service.predict_with_annotation(test_image, conf=0.01)
    
    print(f"Predictions found: {len(predictions)}")
    print(f"Annotated image path: {annotated_path}")
    
    if predictions:
        print(f"Sample prediction: {predictions[0]}")
    
    # Test the controller response format
    print("\n" + "="*50)
    print("Testing controller response format...")
    print(f"image_path format: /static/uploads/049ac5f6-038e-4882-a1c4-a1ee5aac85de.jpg")
    print(f"full URL: http://127.0.0.1:9999/static/uploads/049ac5f6-038e-4882-a1c4-a1ee5aac85de.jpg")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
