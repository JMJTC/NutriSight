# 🍽️ 食物识别模块 - 快速启动指南

> ✅ 所有问题已修复，模块可正常使用！

## 问题修复概述

之前启动应用时的导入错误已成功修复：
- ❌ 错误: `ImportError: cannot import name 'DependUser' from 'app.core.dependency'`
- ✅ 修复: 更正了 `app/api/v1/food/food.py` 中的导入和依赖注入方式

## 📊 系统状态

```
✓ 应用导入成功 (47 个路由)
✓ 8 个食物 API 路由已注册
✓ 5 个数据库模型已加载
✓ YOLO 服务就绪
✓ 数据初始化脚本已集成
```

## 🚀 快速开始

### 1️⃣ 验证系统状态
```bash
python verify_food_module.py
```

**预期输出**:
```
======================================================================
✅ 所有验证通过！食物识别模块准备就绪
======================================================================
```

### 2️⃣ 启动应用
```bash
python run.py
```

**预期输出**:
```
2026-03-05 21:30:57 - INFO - Uvicorn running on http://0.0.0.0:9999
```

### 3️⃣ 访问应用

| 资源 | URL |
|------|-----|
| 🔧 API 文档 | http://localhost:9999/docs |
| 📖 API 文档 (ReDoc) | http://localhost:9999/redoc |
| 🏠 主页 | http://localhost:3100 |

## 📚 可用的 8 个 API 接口

### 1. 食物识别 🥗
```bash
curl -X POST "http://localhost:9999/api/v1/food/recognize" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@food_image.jpg"
```

### 2. 识别历史 📜
```bash
curl "http://localhost:9999/api/v1/food/history?page=1&page_size=10"
```

### 3. 记录详情 📋
```bash
curl "http://localhost:9999/api/v1/food/record/1"
```

### 4. 食物类别列表 📑
```bash
curl "http://localhost:9999/api/v1/food/categories"
```

### 5. 创建食物类别 ➕
```bash
curl -X POST "http://localhost:9999/api/v1/food/categories" \
  -H "Content-Type: application/json" \
  -d '{"name":"Apple","code":0,"food_type":"Fruit"}'
```

### 6. 更新食物类别 ✏️
```bash
curl -X PUT "http://localhost:9999/api/v1/food/categories/1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Red Apple"}'
```

### 7. 添加营养信息 🥕
```bash
curl -X POST "http://localhost:9999/api/v1/food/nutrition" \
  -H "Content-Type: application/json" \
  -d '{"food_id":1,"energy":52.0,"protein":0.26,"fat":0.17,"carbohydrate":13.81,"fiber":2.4,"sodium":2.0}'
```

### 8. 服务状态 🔍
```bash
curl "http://localhost:9999/api/v1/food/status"
```

## 📖 详细文档

- 📄 [完整使用指南](FOOD_RECOGNITION_GUIDE.md) - API 详细说明、数据库结构、故障排除
- 📄 [模块改进总结](FOOD_MODULE_SUMMARY.md) - 改进清单、下一步建议
- 📄 [修复报告](FOOD_MODULE_FIX_REPORT.md) - 问题分析、修复方案

## 🔧 修复技术细节

### 问题代码
```python
# ❌ 错误：导入不存在的依赖
from app.core.dependency import DependUser
```

### 修复方案
```python
# ✅ 正确：使用项目中存在的依赖
from app.core.dependency import DependAuth

@food_router.post("/recognize")
async def recognize_food(
    file: UploadFile = File(...),
    current_user = DependAuth,  # ✅ 正确的注入方式
):
    user_id = current_user.id
```

## ✨ 功能亮点

- 🤖 **YOLO 模型集成**: 支持 best.pt 和 last.pt，自动重试加载
- 🗄️ **完整的数据库模型**: 7 个模型支持完整的业务流程
- 🔐 **JWT 身份认证**: 接口受权限保护
- 📊 **营养分析**: 自动汇总和分析识别到的食物营养信息
- 📝 **详细日志**: 便于问题排查和性能分析
- 🎯 **类型安全**: Pydantic 数据验证

## 📊 初始化数据

应用启动时自动初始化 15 种常见食物：

```
✓ Apple (苹果)
✓ Banana (香蕉)
✓ Orange (橙子)
✓ Carrot (胡萝卜)
✓ Broccoli (西兰花)
✓ Chicken Breast (鸡胸肉)
✓ Beef (牛肉)
✓ Salmon (三文鱼)
✓ Rice (米饭)
✓ Bread (面包)
✓ Egg (鸡蛋)
✓ Milk (牛奶)
✓ Yogurt (酸奶)
✓ Tomato (番茄)
✓ Lettuce (生菜)
```

## 🧪 测试建议

### 单元测试
```bash
pytest app/tests/test_food_module.py -v
```

### API 测试
1. 登录获取 Token
2. 测试各个端点
3. 验证响应格式和数据

### 集成测试
1. 上传食物图片
2. 验证识别结果
3. 检查数据库记录
4. 测试营养聚合

## ⚙️ 系统要求

- **Python**: 3.11+
- **模型文件**: `./weights/best.pt` 或 `./weights/last.pt`
- **依赖**: 已在 pyproject.toml 中声明
  - ultralytics >= 8.4.12
  - opencv-python-headless >= 4.13.0.92

## 🐛 常见问题

### Q: YOLO 模型加载失败
**A**: 检查 `./weights/best.pt` 文件是否存在，运行 `python verify_food_module.py` 诊断

### Q: API 返回 401 Unauthorized
**A**: 在请求头中添加 Token，或使用 `Authorization: Bearer <token>`

### Q: 识别结果为空
**A**: 检查模型是否成功加载，查看服务状态 `/api/v1/food/status`

## 📝 修改文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `app/api/v1/food/food.py` | 修复 | 导入和依赖注入 |
| `verify_food_module.py` | 新增 | 系统验证脚本 |
| `FOOD_MODULE_FIX_REPORT.md` | 新增 | 修复报告 |

## 🎯 下一步建议

1. ✅ 验证系统 - 运行 `python verify_food_module.py`
2. ✅ 启动应用 - 运行 `python run.py`
3. ⏭️ 测试接口 - 访问 http://localhost:9999/docs
4. ⏭️ 开发前端 - 创建食物识别的 Vue 组件
5. ⏭️ 部署上线 - 配置生产环境

---

**状态**: ✅ 完成并可用  
**最后更新**: 2026-03-05  
**维护者**: AI Assistant
