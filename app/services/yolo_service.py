from ultralytics import YOLO
import os
from app.settings.config import settings
import logging

logger = logging.getLogger(__name__)

class YoloService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(YoloService, cls).__new__(cls)
            # 延迟加载模型，或者在实例化时加载
        return cls._instance

    def load_model(self):
        if self._model is not None:
            return

        weights_path = os.path.join(settings.BASE_DIR, "weights", "best.pt")
        if not os.path.exists(weights_path):
             logger.warning(f"Model not found at {weights_path}, trying absolute path or check deployment")
             # Fallback logic if needed, but for now we expect it to be there
             return
        
        try:
            logger.info(f"Loading YOLO model from {weights_path}...")
            self._model = YOLO(weights_path)
            logger.info("YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise e

    def predict(self, image_path: str, conf: float = 0.25):
        if not self._model:
            self.load_model()
        
        if not self._model:
            raise Exception("Model not loaded")
        
        # YOLOv8/v11 predict
        results = self._model.predict(image_path, conf=conf, save=False)
        
        parsed_results = []
        for r in results:
            names = r.names
            for box in r.boxes:
                cls_id = int(box.cls[0])
                parsed_results.append({
                    "class_id": cls_id,
                    "class_name": names[cls_id],
                    "confidence": float(box.conf[0]),
                    "bbox": box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                })
        return parsed_results

yolo_service = YoloService()
