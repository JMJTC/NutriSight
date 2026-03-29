from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class FoodCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="食物名称")
    code: int = Field(..., ge=0, description="YOLO 类别 ID")
    food_type: Optional[str] = Field(None, max_length=50, description="食物类型（蔬菜、肉类、水果等）")
    description: Optional[str] = Field(None, max_length=255, description="食物描述")
    image_url: Optional[str] = Field(None, max_length=255, description="示例图片 URL")


class FoodCategoryCreate(FoodCategoryBase):
    """创建食物类别"""
    pass


class FoodCategoryUpdate(BaseModel):
    """更新食物类别"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    food_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    image_url: Optional[str] = Field(None, max_length=255)


class NutritionBase(BaseModel):
    """营养成分基础信息"""
    energy: float = Field(..., ge=0, description="热量 (kcal/100g)") 
    protein: float = Field(..., ge=0, description="蛋白质 (g/100g)")
    fat: float = Field(..., ge=0, description="脂肪 (g/100g)")
    carbohydrate: float = Field(..., ge=0, description="碳水化合物 (g/100g)")
    fiber: float = Field(default=0.0, ge=0, description="膳食纤维 (g/100g)")
    sodium: float = Field(default=0.0, ge=0, description="钠 (mg/100g)")

    @validator('energy', 'protein', 'fat', 'carbohydrate')
    def validate_reasonable_values(cls, v):
        """验证营养值在合理范围内"""
        if v > 1000:
            raise ValueError('营养值过大，请检查输入')
        return v


class NutritionCreate(NutritionBase):
    """创建营养信息"""
    food_id: int = Field(..., description="食物类别 ID")


class RecognitionResult(BaseModel):
    """单个识别结果"""
    class_id: int = Field(..., description="YOLO 类别 ID")
    class_name: str = Field(..., description="食物名称")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度 (0-1)")
    bbox: List[float] = Field(..., description="边界框 [x1, y1, x2, y2]")
    nutrition: Optional[NutritionBase] = Field(None, description="营养信息")

    @validator('bbox')
    def validate_bbox(cls, v):
        """验证边界框格式"""
        if len(v) != 4:
            raise ValueError('bbox 必须包含 4 个坐标值')
        if not all(isinstance(x, (int, float)) for x in v):
            raise ValueError('bbox 坐标必须是数字')
        # 允许 [0,0,0,0] 作为分类回退结果（无确定检测框）
        if v == [0, 0, 0, 0]:
            return v
        if v[0] >= v[2] or v[1] >= v[3]:
            raise ValueError('bbox 坐标无效')
        return v


class RecognitionResponse(BaseModel):
    """食物识别响应"""
    record_id: int = Field(..., description="识别记录 ID")
    image_path: str = Field(..., description="图片相对路径")
    results: List[RecognitionResult] = Field(..., description="识别结果列表")
    total_nutrition: Optional[NutritionBase] = Field(None, description="总营养信息")
    created_at: str = Field(..., description="创建时间")


class RecognitionHistoryItem(BaseModel):
    """识别历史项"""
    id: int = Field(..., description="记录 ID")
    image_path: str = Field(..., description="图片路径")
    created_at: str = Field(..., description="创建时间")
    status: str = Field(..., description="识别状态")
    total_energy: float = Field(..., description="总热量")


class AnalysisResponse(BaseModel):
    """营养分析响应"""
    total_energy: float = Field(..., ge=0, description="总热量")
    total_protein: float = Field(..., ge=0, description="总蛋白质")
    total_fat: float = Field(..., ge=0, description="总脂肪")
    total_carbohydrate: float = Field(..., ge=0, description="总碳水化合物")
    summary: str = Field(..., description="分析摘要")
    suggestion: Optional[str] = Field(None, description="营养建议")


class NutritionResponse(BaseModel):
    """营养信息响应"""
    id: int = Field(..., description="营养信息 ID")
    food_id: int = Field(..., description="食物类别 ID")
    food_name: str = Field(..., description="食物名称")
    energy: float = Field(..., ge=0, description="热量 (kcal/100g)")
    protein: float = Field(..., ge=0, description="蛋白质 (g/100g)")
    fat: float = Field(..., ge=0, description="脂肪 (g/100g)")
    carbohydrate: float = Field(..., ge=0, description="碳水化合物 (g/100g)")
    fiber: float = Field(default=0.0, ge=0, description="膳食纤维 (g/100g)")
    sodium: float = Field(default=0.0, ge=0, description="钠 (mg/100g)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class FoodCategoryResponse(BaseModel):
    """食物类别响应"""
    id: int = Field(..., description="食物类别 ID")
    name: str = Field(..., description="食物名称")
    code: int = Field(..., description="YOLO 类别 ID")
    food_type: Optional[str] = Field(None, description="食物类型")
    description: Optional[str] = Field(None, description="食物描述")
    image_url: Optional[str] = Field(None, description="示例图片 URL")
    nutrition: Optional[NutritionResponse] = Field(None, description="关联的营养信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
