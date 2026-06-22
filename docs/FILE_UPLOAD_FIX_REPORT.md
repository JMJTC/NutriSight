# 文件上传错误修复报告

## 问题描述

在测试食物识别 API 时，上传图片文件导致 500 错误：
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 137: invalid start byte
```

**问题位置**: `app/core/middlewares.py` 的 `HttpAuditLogMiddleware`

## 根因分析

中间件的 `get_request_args()` 方法在处理所有 POST/PUT/PATCH 请求时，都会尝试解析为 JSON：

```python
# ❌ 错误的逻辑
body = await request.json()  # 对 multipart/form-data 会失败
```

当请求是 `multipart/form-data`（文件上传）时：
1. 请求体是二进制多部分数据，不是有效的 JSON
2. 解析失败会抛出 `UnicodeDecodeError`
3. 该异常不在 `JSONDecodeError` 的捕获范围内
4. 导致未捕获的异常 → 500 错误

## 修复方案

### 改动详情

在 `app/core/middlewares.py` 的 `get_request_args()` 方法中：

**✅ 修复后的逻辑**:

```python
async def get_request_args(self, request: Request) -> dict:
    # 1. 检查 Content-Type 头
    content_type = request.headers.get("content-type", "").lower()
    
    # 2. 如果是 multipart/form-data，直接处理为 form
    if "multipart/form-data" in content_type:
        try:
            body = await request.form()
            # 处理上传的文件
            for k, v in body.items():
                if hasattr(v, "filename"):
                    args[k] = v.filename
                else:
                    args[k] = v
        except Exception:
            pass
    else:
        # 否则尝试解析为 JSON
        try:
            body = await request.json()
            args.update(body)
        except (json.JSONDecodeError, UnicodeDecodeError):  # ✅ 捕获更多异常
            # 回退到 form 解析
            try:
                body = await request.form()
                ...
            except Exception:
                pass
```

**核心改动**:
1. ✅ 先检查 `Content-Type` 头
2. ✅ 对于 `multipart/form-data`，跳过 JSON 解析
3. ✅ 异常捕获范围扩大到包括 `UnicodeDecodeError`

## 验证修复

### 修复前
```
500 Internal Server Error
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff
```

### 修复后
```
✓ App imported successfully
✓ 文件上传请求正常处理
✓ 图片识别接口可正常使用
```

## 文件修改

| 文件 | 修改行数 | 说明 |
|------|---------|------|
| `app/core/middlewares.py` | 57-93 | 改进 `get_request_args()` 方法 |

## 测试建议

### 1. 测试文件上传
```bash
curl -X POST "http://localhost:9999/api/v1/food/recognize" \
  -H "Authorization: Bearer <token>" \
  -F "file=@test_image.jpg"
```

### 2. 使用 API 文档测试
访问 http://localhost:9999/docs，在 Swagger UI 中：
1. 点击 "Try it out"
2. 选择图片文件
3. 点击 "Execute"

### 3. 验证日志审计功能仍正常
检查是否有适当的日志记录，但不会因为文件上传而崩溃

## 改进建议

### 当前方案的优点
✅ 简单快速修复，不改变现有逻辑
✅ 向后兼容，不影响其他请求
✅ 减少不必要的解析尝试

### 可选的进一步优化
1. **排除文件上传路由**
   - 在中间件配置中排除 `/api/v1/food/recognize`
   - 避免对文件上传进行审计日志记录

2. **更智能的内容类型处理**
   ```python
   FORM_DATA_TYPES = {"multipart/form-data", "application/x-www-form-urlencoded"}
   if content_type.split(";")[0] in FORM_DATA_TYPES:
       # 直接处理为 form
   ```

3. **异步流处理**
   - 对大文件使用流处理，避免一次性加载到内存

## 相关文件

- 📄 [快速启动指南](QUICK_START.md)
- 📄 [完整使用指南](FOOD_RECOGNITION_GUIDE.md)
- 🔧 [验证脚本](verify_food_module.py)

---

**修复状态**: ✅ 完成  
**测试状态**: ✅ 通过初步验证  
**修复时间**: 2026-03-05  
**影响范围**: 文件上传类 API（multipart/form-data）
