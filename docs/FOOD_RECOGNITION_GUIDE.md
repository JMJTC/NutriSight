# 食物识别模块完整指南

## 概述

本文档介绍项目中的食物识别模块完善说明，包括YOLO模型推理、识别记录管理、营养分析等功能。

## 模块架构

```
食物识别模块 (Food Recognition Module)
├── 数据模型 (Models)
│   ├── FoodCategory - 食物类别
│   ├── Nutrition - 营养成分信息
│   ├── RecognitionRecord - 识别记录
│   ├── RecognitionDetail - 识别详情
│   ├── NutritionAnalysis - 营养分析结果
│   ├── UserProfile - 用户扩展信息
│   └── NutritionRecommendation - 营养推荐
├── 业务服务 (Services)
│   └── YOLO Service - 模型推理服务
├── 控制器 (Controllers)
│   └── FoodController - 食物业务控制器
├── API 路由 (Routes)
│   └── /api/v1/food/* - RESTful API 接口
└── 初始化脚本 (Scripts)
    └── init_food_data.py - 数据库初始化脚本
```

## 核心功能

### 1. 食物识别 (Food Recognition)

**端点**: `POST /api/v1/food/recognize`

**功能**: 上传图片进行食物识别

**请求**:
```bash
curl -X POST "http://localhost:9999/api/v1/food/recognize" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@food_image.jpg"
```

**响应示例**:
```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "record_id": 1,
    "image_path": "/static/uploads/uuid.jpg",
    "results": [
      {
        "class_id": 0,
        "class_name": "Apple",
        "confidence": 0.95,
        "bbox": [100, 150, 300, 350],
        "nutrition": {
          "energy": 52.0,
          "protein": 0.26,
          "fat": 0.17,
          "carbohydrate": 13.81,
          "fiber": 2.4,
          "sodium": 2.0
        }
      }
    ],
    "total_nutrition": {
      "energy": 52.0,
      "protein": 0.26,
      "fat": 0.17,
      "carbohydrate": 13.81,
      "fiber": 2.4,
      "sodium": 2.0
    },
    "created_at": "2026-03-05 14:30:00"
  }
}
```

### 2. 识别历史 (Recognition History)

**端点**: `GET /api/v1/food/history`

**参数**:
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 10)

**功能**: 获取用户的食物识别历史

**响应示例**:
```json
{
  "code": 200,
  "msg": "OK",
  "data": [
    {
      "id": 1,
      "image_path": "/static/uploads/uuid.jpg",
      "created_at": "2026-03-05 14:30:00",
      "status": "success",
      "total_energy": 52.0
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10
}
```

### 3. 识别记录详情 (Record Detail)

**端点**: `GET /api/v1/food/record/{record_id}`

**功能**: 获取单条识别记录的详细信息

**响应**:
返回与识别接口相同的详细格式，包含所有识别的食物和营养信息。

### 4. 食物类别管理 (Category Management)

**获取列表** - `GET /api/v1/food/categories`
```bash
curl "http://localhost:9999/api/v1/food/categories?page=1&page_size=20"
```

**创建类别** - `POST /api/v1/food/categories`
```bash
curl -X POST "http://localhost:9999/api/v1/food/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Apple",
    "code": 0,
    "food_type": "Fruit",
    "description": "Fresh apple",
    "image_url": "https://example.com/apple.jpg"
  }'
```

**更新类别** - `PUT /api/v1/food/categories/{category_id}`
```bash
curl -X PUT "http://localhost:9999/api/v1/food/categories/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Red Apple",
    "food_type": "Fruit"
  }'
```

### 5. 营养信息管理 (Nutrition Management)

**添加营养信息** - `POST /api/v1/food/nutrition`
```bash
curl -X POST "http://localhost:9999/api/v1/food/nutrition" \
  -H "Content-Type: application/json" \
  -d '{
    "food_id": 1,
    "energy": 52.0,
    "protein": 0.26,
    "fat": 0.17,
    "carbohydrate": 13.81,
    "fiber": 2.4,
    "sodium": 2.0
  }'
```

### 6. 服务状态 (Service Status)

**端点**: `GET /api/v1/food/status`

**功能**: 获取 YOLO 服务和数据库状态

**响应示例**:
```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "yolo_model": {
      "loaded": true,
      "ready": true,
      "error": null,
      "model_path": "f:\\...\\weights\\best.pt"
    },
    "database": {
      "total_categories": 15,
      "total_records": 3
    },
    "status": "ready"
  }
}
```

## 关键改进

### 1. YOLO 服务增强

**文件**: `app/services/yolo_service.py`

**改进内容**:
- ✅ 单例模式确保只加载一次模型
- ✅ 自动重试加载机制
- ✅ 多路径模型查找（best.pt 和 last.pt）
- ✅ 详细的错误日志和状态跟踪
- ✅ 支持置信度阈值配置
- ✅ 返回类名和置信度信息

### 2. 控制器业务逻辑完善

**文件**: `app/controllers/food.py`

**新增方法**:
- `recognize_food()` - 食物识别主方法
- `get_history()` - 获取识别历史
- `get_record_detail()` - 获取记录详情
- `get_food_categories()` - 获取食物类别列表
- `create_food_category()` - 创建食物类别
- `update_food_category()` - 更新食物类别
- `add_nutrition_info()` - 添加营养信息
- `get_service_status()` - 获取服务状态

**特性**:
- 完整的异常处理和错误消息
- 数据验证和唯一性检查
- 营养信息聚合和分析
- 详细的日志记录

### 3. 数据验证增强

**文件**: `app/schemas/food.py`

**改进内容**:
- ✅ 使用 Field 添加详细的字段描述
- ✅ 范围验证（最小/最大值）
- ✅ 自定义验证器（bbox 格式、营养值范围）
- ✅ 更详细的文档字符串

### 4. API 路由完善

**文件**: `app/api/v1/food/food.py`

**特性**:
- ✅ 完整的 RESTful API 设计
- ✅ 统一的响应格式（Success/Fail）
- ✅ 完整的错误处理
- ✅ OpenAPI/Swagger 文档支持

### 5. 数据库初始化

**文件**: `app/scripts/init_food_data.py`

**包含数据**:
- 15 种常见食物类别（水果、蔬菜、肉类、谷物等）
- 每种食物的营养信息（热量、蛋白质、脂肪等）
- 自动去重和跳过已存在的数据

**集成方式**:
- 自动在应用启动时初始化
- 支持手动运行脚本
- 支持清除数据的操作

### 6. 应用启动自动初始化

**文件**: `app/core/init_app.py`

**修改**:
- 添加 `init_food_data()` 函数
- 在 `init_data()` 中调用，确保应用启动时自动初始化食物数据

## 快速开始

### 1. 启动应用

```bash
# 进入项目根目录
cd vue-fastapi-admin

# 启动后端服务
python run.py
```

### 2. 验证功能

访问 API 文档: http://localhost:9999/docs

### 3. 测试食物识别

```bash
# 使用 curl 上传图片进行识别
curl -X POST "http://localhost:9999/api/v1/food/recognize" \
  -F "file=@test_food_image.jpg"
```

### 4. 检查初始化数据

```bash
# 查看食物类别列表
curl "http://localhost:9999/api/v1/food/categories"

# 查看服务状态
curl "http://localhost:9999/api/v1/food/status"
```

## 系统要求

### Python 依赖

已在 `pyproject.toml` 中添加：
- `ultralytics>=8.4.12` - YOLO 模型框架
- `opencv-python-headless>=4.13.0.92` - 图像处理

### 模型文件

需要将训练好的 YOLO 模型放在:
- `./weights/best.pt` - 推荐使用的模型
- `./weights/last.pt` - 备选模型

### 磁盘空间

- YOLO 模型: ~100-200 MB
- 上传的图片: 按需分配（建议 1GB+）

## 数据库表结构

### FoodCategory（食物类别）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | varchar | 食物名称 |
| code | int | YOLO 类别 ID |
| food_type | varchar | 食物类型 |
| description | varchar | 描述 |
| image_url | varchar | 示例图片 URL |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Nutrition（营养成分）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| food_id | int | 食物 ID（外键） |
| energy | float | 热量 (kcal/100g) |
| protein | float | 蛋白质 (g/100g) |
| fat | float | 脂肪 (g/100g) |
| carbohydrate | float | 碳水化合物 (g/100g) |
| fiber | float | 膳食纤维 (g/100g) |
| sodium | float | 钠 (mg/100g) |

### RecognitionRecord（识别记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| user_id | int | 用户 ID（外键） |
| image_path | varchar | 图片路径 |
| status | varchar | 识别状态 |
| created_at | datetime | 创建时间 |

### RecognitionDetail（识别详情）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| record_id | int | 识别记录 ID（外键） |
| food_id | int | 食物 ID（外键） |
| confidence | float | 识别置信度 |
| bbox | json | 边界框坐标 |

## 故障排除

### 问题 1: YOLO 模型加载失败

**症状**: 错误消息 "YOLO model not found"

**解决方案**:
1. 检查 `weights` 目录是否存在
2. 确保 `best.pt` 或 `last.pt` 文件存在
3. 检查文件权限
4. 查看日志 `/api/v1/food/status`

### 问题 2: 识别结果为空

**症状**: 返回结果为空列表

**解决方案**:
1. 检查模型是否正确加载
2. 尝试调整置信度阈值（目前默认 0.25）
3. 确认图片格式支持（jpg, png, bmp, webp）
4. 检查图片中是否包含训练数据中的食物

### 问题 3: 数据库初始化失败

**症状**: 应用启动时数据库错误

**解决方案**:
1. 确保数据库文件有写权限
2. 手动运行迁移: `aerich upgrade`
3. 清除旧的迁移文件并重新生成

## 未来改进方向

1. **性能优化**
   - 实现异步地批量推理
   - 添加 GPU 支持
   - 实现推理结果缓存

2. **功能扩展**
   - 支持多模型选择
   - 添加食物重量估算
   - 实现自定义营养建议引擎

3. **用户体验**
   - 前端食物识别界面
   - 识别历史统计分析
   - 营养目标追踪

## 相关文件

- 模型服务: [app/services/yolo_service.py](app/services/yolo_service.py)
- 业务逻辑: [app/controllers/food.py](app/controllers/food.py)
- API 路由: [app/api/v1/food/food.py](app/api/v1/food/food.py)
- 数据模型: [app/models/food.py](app/models/food.py)
- 数据验证: [app/schemas/food.py](app/schemas/food.py)
- 数据初始化: [app/scripts/init_food_data.py](app/scripts/init_food_data.py)
- 应用初始化: [app/core/init_app.py](app/core/init_app.py)

---

**更新时间**: 2026-03-05  
**版本**: 1.0  
**状态**: ✅ 完成并可用
