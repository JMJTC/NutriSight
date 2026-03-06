import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
from ultralytics import YOLO

from app.settings.config import settings

logger = logging.getLogger(__name__)


class YoloService:
    """单例 YOLO 服务，负责模型加载和推理"""
    _instance = None
    _model = None
    _model_loaded = False
    _load_error = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(YoloService, cls).__new__(cls)
        return cls._instance

    def _get_model_path(self) -> Path:
        """获取模型路径，支持多个位置的查找"""
        # 优先查找 best.pt
        best_model = Path(settings.BASE_DIR) / "weights" / "best.pt"
        if best_model.exists():
            return best_model
        
        # 备选方案：查找 last.pt
        last_model = Path(settings.BASE_DIR) / "weights" / "last.pt"
        if last_model.exists():
            return last_model
        
        # 如果找不到，返回 best.pt 路径（便于错误提示）
        return best_model

    def load_model(self) -> bool:
        """
        加载 YOLO 模型
        
        Returns:
            bool: 模型是否成功加载
        """
        if self._model is not None and self._model_loaded:
            logger.debug("YOLO model already loaded")
            return True

        if self._load_error:
            logger.error(f"Previous model loading failed: {self._load_error}")
            return False

        model_path = self._get_model_path()
        
        if not model_path.exists():
            error_msg = f"YOLO model not found at {model_path}"
            logger.error(error_msg)
            self._load_error = error_msg
            return False
        
        try:
            logger.info(f"Loading YOLO model from {model_path}...")
            self._model = YOLO(str(model_path))
            self._model_loaded = True
            logger.info("YOLO model loaded successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to load YOLO model: {str(e)}"
            logger.error(error_msg)
            self._load_error = error_msg
            self._model = None
            self._model_loaded = False
            return False

    def is_ready(self) -> bool:
        """检查服务是否就绪"""
        if not self._model_loaded:
            return self.load_model()
        return self._model is not None

    def predict(self, image_path: str, conf: float = 0.25) -> List[Dict]:
        """
        对图片进行食物识别预测
        
        Args:
            image_path (str): 图片路径
            conf (float): 置信度阈值，默认 0.25
            
        Returns:
            List[Dict]: 预测结果列表，每个结果包含 class_id, class_name, confidence, bbox
            
        Raises:
            Exception: 模型未加载或推理失败
        """
        if not self.is_ready():
            raise Exception(f"YOLO model is not ready: {self._load_error}")
        
        if self._model is None:
            raise Exception("YOLO model is None, model not properly loaded")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            logger.info(f"Running YOLO prediction on {image_path}")
            results = self._model.predict(image_path, conf=conf, save=False, verbose=False)
            
            # 检查 results 是否为 None
            if results is None:
                logger.warning("YOLO predict returned None")
                return []
            
            # 检查 results 是否可迭代
            try:
                iter(results)
            except TypeError:
                logger.warning(f"YOLO predict returned non-iterable result: {type(results)}")
                return []
            
            parsed_results = []
            for result in results:
                if result is None:
                    continue
                    
                names = result.names
                if result.boxes is None or len(result.boxes) == 0:
                    logger.debug(f"No objects detected in image")
                    continue
                    
                for box in result.boxes:
                    try:
                        cls_id = int(box.cls[0].item())
                        confidence = float(box.conf[0].item())
                        
                        parsed_results.append({
                            "class_id": cls_id,
                            "class_name": names.get(cls_id, f"Unknown_{cls_id}"),
                            "confidence": confidence,
                            "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                        })
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"Failed to parse box data: {str(e)}")
                        continue
            
            logger.info(f"Prediction completed. Found {len(parsed_results)} objects")
            return parsed_results
        except Exception as e:
            error_msg = f"Prediction failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_status(self) -> Dict[str, any]:
        """获取服务状态"""
        return {
            "loaded": self._model_loaded,
            "ready": self.is_ready(),
            "error": self._load_error,
            "model_path": str(self._get_model_path())
        }


# 全局单例实例
yolo_service = YoloService()
