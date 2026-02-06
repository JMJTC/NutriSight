from typing import List, Optional
from pydantic import BaseModel

class FoodCategoryBase(BaseModel):
    name: str
    code: int
    food_type: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class FoodCategoryCreate(FoodCategoryBase):
    pass

class FoodCategoryUpdate(BaseModel):
    name: Optional[str] = None
    food_type: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class NutritionBase(BaseModel):
    energy: float
    protein: float
    fat: float
    carbohydrate: float
    fiber: float
    sodium: float

class NutritionCreate(NutritionBase):
    food_id: int

class RecognitionResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]
    nutrition: Optional[NutritionBase] = None

class RecognitionResponse(BaseModel):
    record_id: int
    image_path: str
    results: List[RecognitionResult]
    total_nutrition: Optional[NutritionBase] = None
    created_at: str

class AnalysisResponse(BaseModel):
    total_energy: float
    total_protein: float
    total_fat: float
    total_carbohydrate: float
    summary: str
    suggestion: str
