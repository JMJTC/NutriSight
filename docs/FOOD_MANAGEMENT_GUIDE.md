# 食物管理模块 - 快速开始

## 功能概述

食物管理界面提供了对食物类别和营养信息的完整增删改查（CRUD）功能，支持图片上传、营养数据管理等特性。

## 菜单位置

在应用左侧菜单中：**食物识别 > 食物管理**

## 主要功能

### 1. 查看食物列表

- 显示所有已创建的食物类别
- 支持按名称搜索食物
- 分页加载，每页显示灵活个数
- 列表展示内容：
  - 食物名称
  - YOLO ID（类别识别ID）
  - 食物类型（蔬菜、肉类、水果等）
  - 热量、蛋白质等营养信息预览
  - 示例图片
  - 描述信息

### 2. 创建食物类别

点击 **"新增食物"** 按钮打开编辑对话框

#### 基本信息部分：
- **食物名称**（必填）：输入唯一的食物名称
- **YOLO 类别 ID**（必填）：从YOLO模型对应的类别ID，后不可修改
- **食物类型**（可选）：从预设列表选择或自定义
- **描述**（可选）：食物的简短描述

#### 图片上传部分：
- 支持 jpg, png 等常见图片格式
- 点击上传区域选择本地图片
- 图片将自动保存至服务器

#### 营养信息部分（每100g）：
- **热量**（kcal）
- **蛋白质**（g）
- **脂肪**（g）
- **碳水化合物**（g）
- **膳食纤维**（g）
- **钠**（mg）

### 3. 编辑食物信息

点击列表中的 **"编辑"** 按钮

可修改内容：
- 食物类型、描述
- 食物图片（可上传新图片替换）
- 所有营养数据

**注意**：食物名称和YOLO ID 在创建后无法修改

### 4. 更新营养信息

在编辑对话框中修改"营养信息"部分的任何字段，点击"请求"即可保存

### 5. 删除食物类别

点击列表中的 **"删除"** 按钮

- 会弹出确认框：确认删除此食物及其营养信息吗？
- 确认后食物及其关联的营养数据将被级联删除
- 这将影响基于该食物的所有识别记录

## API 端点参考

### GET /food/categories
获取食物类别列表（分页）

**参数：**
- `page` (int): 页码，默认1
- `page_size` (int): 每页数量，默认20
- `search` (string): 按名称搜索

**响应：**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Apple",
        "code": 0,
        "food_type": "Fruit",
        "description": "Fresh apple",
        "image_url": "/static/uploads/food_images/xxx.png",
        "nutrition": {
          "id": 1,
          "energy": 52.0,
          "protein": 0.26,
          ...
        },
        "created_at": "2026-03-29T10:00:00",
        "updated_at": "2026-03-29T10:00:00"
      }
    ],
    "total": 15,
    "page": 1,
    "page_size": 20
  }
}
```

### POST /food/categories/upload
创建食物类别（支持图片和营养信息）

**请求类型：** multipart/form-data

**参数：**
- `name` (string, required): 食物名称
- `code` (int, required): YOLO 类别 ID
- `food_type` (string, optional): 食物类型
- `description` (string, optional): 描述
- `image` (file, optional): 图片文件
- `nutrition` (JSON string, optional): 营养信息JSON

**营养信息 JSON 格式：**
```json
{
  "energy": 52.0,
  "protein": 0.26,
  "fat": 0.17,
  "carbohydrate": 13.81,
  "fiber": 2.4,
  "sodium": 2.0
}
```

### GET /food/categories/{category_id}
获取单个食物的详细信息

### PUT /food/categories/{category_id}/upload
更新食物类别（支持图片和营养信息更新）

**请求类型：** multipart/form-data

**参数：** 同创建接口（除了name和code）

### DELETE /food/categories/{category_id}
删除食物类别及级联删除营养信息

### PUT /food/nutrition/{food_id}
仅更新食物的营养信息

**请求类型：** application/x-www-form-urlencoded

**参数：**
- `energy`, `protein`, `fat`, `carbohydrate`, `fiber`, `sodium`

## 数据关系

```
FoodCategory (食物类别)
├── id: 主键
├── name: 唯一的食物名称
├── code: 唯一的YOLO类别ID
├── food_type: 食物类型
├── description: 描述
├── image_url: 图片URL
└── nutrition: (OneToOne关系) → Nutrition

Nutrition (营养信息)
├── id: 主键
├── food: (OneToOne) → FoodCategory
├── energy, protein, fat, carbohydrate, fiber, sodium
└── timestamps
```

## 常见问题

**Q: 能否修改YOLO ID？**
A: 不能。YOLO ID 在食物创建时确定后无法修改。如需修改，需要删除后重新创建。

**Q: 删除食物会影响已有的识别记录吗？**
A: 删除食物类别仅会删除其营养信息。已有的识别记录仍保留，但关联的营养数据会丢失。

**Q: 支持批量导入食物吗？**
A: 当前不支持。可使用 `app/scripts/init_food_data.py` 脚本初始化默认食物数据。

**Q: 上传的图片大小有限制吗？**
A: 建议不超过 5MB。图片会保存至 `/deploy/static/uploads/food_images/` 目录。
