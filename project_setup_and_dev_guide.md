# 项目二开指南与文档

## 1. 项目编译与运行

本项目采用前后端分离架构，后端基于 FastAPI，前端基于 Vue3 + Naive UI。

### 1.1 环境准备
- **Node.js**: v18+ (建议 v20 或 v22)
- **Python**: 3.11+
- **包管理器**:
  - 后端: `uv` (推荐)
  - 前端: `pnpm`

### 1.2 后端启动 (FastAPI)
1. 进入项目根目录。
2. 安装依赖：
   ```bash
   uv sync
   ```
3. 启动服务：
   ```bash
   uv run run.py
   ```
   服务将运行在 `http://0.0.0.0:9999`。
   API 文档地址: `http://localhost:9999/docs`

### 1.3 前端启动 (Vue3)
1. 进入 `web` 目录：
   ```bash
   cd web
   ```
2. 安装依赖：
   ```bash
   pnpm install
   ```
3. 启动开发服务器：
   ```bash
   pnpm dev
   ```
   服务将运行在 `http://localhost:3100`。

---

## 2. 项目结构说明

### 后端结构 (`app/`)
- `api/v1/`: API 路由定义，按模块划分（如 users, roles）。
  - `apis/`: API 接口管理模块。
  - `__init__.py`: 路由注册入口。
- `core/`: 核心配置与中间件 (config, security, middleware)。
- `models/`: Tortoise ORM 数据模型。
  - `__init__.py`: 模型注册入口。
- `schemas/`: Pydantic 数据验证模型 (DTO)。
- `services/` (可选): 业务逻辑层（当前项目逻辑多在 controllers/api 中）。
- `controllers/`: 控制器层，处理业务逻辑。
- `deploy/`: 部署相关文件。

### 前端结构 (`web/src/`)
- `api/`: API 请求封装 (`index.js` 包含所有请求)。
- `views/`: 页面组件，按功能划分。
- `router/routes/`: 路由定义。
- `components/`: 公共组件。
- `store/`: Pinia 状态管理。
- `utils/`: 工具函数。

---

## 3. 二开方案与步骤建议

根据需求，我们需要增加“食物识别”、“营养信息管理”、“营养分析”等模块。

### 3.1 后端开发计划

#### 第一步：数据模型设计 (`app/models/`)
新建 `food.py`，定义以下模型：
1. **FoodCategory**: 食物类别（对应 YOLO 识别的类别）。
   - 字段: `id`, `name`, `code` (YOLO label id), `calories`, `protein`, `fat`, `carbs`.
2. **FoodLog**: 用户上传记录。
   - 字段: `id`, `user_id`, `image_path`, `recognition_result` (JSON), `created_at`.
3. **NutritionAnalysis**: 营养分析结果。
   - 字段: `id`, `log_id`, `summary`, `suggestion`.

**操作**:
- 在 `app/models/` 下创建 `food.py`。
- 在 `app/models/__init__.py` 中导入新模型。

#### 第二步：业务逻辑与 API 实现 (`app/api/v1/` & `app/controllers/`)
1. **上传与识别接口**:
   - 路径: `POST /api/v1/food/recognize`
   - 功能: 接收图片 -> 校验 -> 保存 -> 调用 YOLO 模型 -> 返回识别结果。
   - 实现: 集成 YOLOv11 (需安装 `ultralytics`)。
2. **营养信息管理接口**:
   - 路径: `CRUD /api/v1/food/category`
   - 功能: 管理员维护食物营养数据。
3. **分析与推荐接口**:
   - 路径: `GET /api/v1/food/analysis/{log_id}`
   - 功能: 根据识别结果计算总热量，生成建议。

**操作**:
- 创建 `app/api/v1/food/` 目录。
- 创建 `app/schemas/food.py` 定义请求/响应结构。
- 创建 `app/controllers/food.py` 实现逻辑。
- 在 `app/api/v1/__init__.py` 中注册 `food_router`。

### 3.2 前端开发计划

#### 第一步：API 封装 (`web/src/api/`)
- 在 `web/src/api/index.js` 或新建 `food.js` 中添加：
  - `uploadFoodImage`
  - `getNutritionInfo`
  - `getFoodAnalysis`

#### 第二步：页面开发 (`web/src/views/`)
1. **食物识别页 (`views/food/recognition/index.vue`)**:
   - 上传组件 (Upload)。
   - 展示识别结果 (Image + Bounding Boxes / List)。
   - 展示营养概览。
2. **营养分析页 (`views/food/analysis/index.vue`)**:
   - 图表展示 (ECharts/Naive UI Charts)。
   - 文字建议展示。
3. **数据管理页 (`views/food/manage/index.vue`)**:
   - 表格展示食物库，支持增删改查。

#### 第三步：路由配置 (`web/src/router/routes/`)
- 添加 `/food` 路由模块，包含上述子页面。

---

## 4. 详细开发步骤

1. **环境准备**: 确保已安装 `ultralytics` (YOLO) 和相关依赖。
   ```bash
   uv pip install ultralytics
   ```
2. **后端 - 模型创建**: 定义 `FoodCategory` 和 `FoodLog`。
3. **后端 - 识别服务**: 编写 YOLO 调用类，加载模型（建议单例模式）。
4. **后端 - 接口开发**: 实现上传接口，串联识别服务。
5. **前端 - 基础页面**: 搭建上传页面骨架。
6. **前后端联调**: 测试图片上传与结果返回。
7. **后端 - 营养逻辑**: 实现营养计算与推荐算法。
8. **前端 - 结果展示**: 完善结果页与图表展示。
9. **测试与优化**: 异常处理（图片格式、大小、识别失败）。

## 5. 注意事项
- **文件存储**: 图片建议存储在本地静态目录或对象存储（OSS），需配置静态资源服务。
- **模型加载**: YOLO 模型较大，建议在应用启动时加载，避免每次请求加载。
- **异步处理**: 如果识别耗时较长，考虑使用后台任务 (BackgroundTasks)。
