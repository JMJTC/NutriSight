from tortoise import fields
from .base import BaseModel, TimestampMixin

class UserProfile(BaseModel, TimestampMixin):
    """用户扩展信息表"""
    user = fields.OneToOneField("models.User", related_name="profile", description="关联用户")
    gender = fields.CharField(max_length=10, null=True, description="性别")
    age = fields.IntField(null=True, description="年龄")
    height = fields.FloatField(null=True, description="身高(cm)")
    weight = fields.FloatField(null=True, description="体重(kg)")

    class Meta:
        table = "user_profile"

class FoodCategory(BaseModel, TimestampMixin):
    """食物类别表"""
    name = fields.CharField(max_length=100, unique=True, description="食物名称")
    chinese_name = fields.CharField(max_length=100, null=True, description="食物中文名称")
    code = fields.IntField(unique=True, description="YOLO类别ID")
    food_type = fields.CharField(max_length=50, null=True, description="食物类型")
    description = fields.CharField(max_length=255, null=True, description="描述")
    image_url = fields.CharField(max_length=255, null=True, description="示例图片URL")

    class Meta:
        table = "food_category"

class Nutrition(BaseModel, TimestampMixin):
    """营养成分表"""
    food = fields.OneToOneField("models.FoodCategory", related_name="nutrition", description="关联食物")
    energy = fields.FloatField(default=0.0, description="热量(kcal/100g)")
    protein = fields.FloatField(default=0.0, description="蛋白质(g)")
    fat = fields.FloatField(default=0.0, description="脂肪(g)")
    carbohydrate = fields.FloatField(default=0.0, description="碳水(g)")
    fiber = fields.FloatField(default=0.0, description="膳食纤维(g)")
    sodium = fields.FloatField(default=0.0, description="钠(mg)")

    class Meta:
        table = "nutrition"

class RecognitionRecord(BaseModel, TimestampMixin):
    """识别记录表"""
    user = fields.ForeignKeyField("models.User", related_name="recognition_records", description="关联用户")
    image_path = fields.CharField(max_length=255, description="原始图片路径")
    annotated_image_path = fields.CharField(max_length=255, null=True, description="标注图片路径")
    status = fields.CharField(max_length=20, default="pending", description="状态: pending/success/failed")
    
    class Meta:
        table = "recognition_record"

class RecognitionDetail(BaseModel, TimestampMixin):
    """识别详情表"""
    record = fields.ForeignKeyField("models.RecognitionRecord", related_name="details", description="关联记录")
    food = fields.ForeignKeyField("models.FoodCategory", related_name="recognition_details", description="识别到的食物")
    confidence = fields.FloatField(description="置信度")
    bbox = fields.JSONField(description="边界框坐标 [x1, y1, x2, y2]")
    
    class Meta:
        table = "recognition_detail"

class NutritionAnalysis(BaseModel, TimestampMixin):
    """营养分析结果表"""
    record = fields.OneToOneField("models.RecognitionRecord", related_name="analysis", description="关联识别记录")
    total_energy = fields.FloatField(default=0.0, description="总热量")
    total_protein = fields.FloatField(default=0.0, description="总蛋白质")
    total_fat = fields.FloatField(default=0.0, description="总脂肪")
    total_carbohydrate = fields.FloatField(default=0.0, description="总碳水")
    total_fiber = fields.FloatField(default=0.0, description="总膳食纤维")
    total_sodium = fields.FloatField(default=0.0, description="总钠")
    summary = fields.TextField(null=True, description="分析总结")
    
    class Meta:
        table = "nutrition_analysis"

class NutritionRecommendation(BaseModel, TimestampMixin):
    """营养推荐表"""
    user = fields.ForeignKeyField("models.User", related_name="recommendations", description="关联用户")
    record = fields.ForeignKeyField("models.RecognitionRecord", related_name="recommendations", null=True, description="关联识别记录")
    content = fields.TextField(description="推荐内容")
    reference = fields.CharField(max_length=255, null=True, description="推荐依据")
    
    class Meta:
        table = "nutrition_recommendation"
