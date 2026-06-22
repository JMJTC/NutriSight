# 食物管理模块调试指南

## 问题：新增食物类别时保存无响应

### 快速诊断步骤

#### 1. 打开浏览器开发者工具
- **Chrome/Edge**: F12 或 右键 → 检查
- 切换到 **Console** 标签页

#### 2. 新增食物类别并点击保存
- 观察Console中的日志输出
- 检查是否有红色错误信息

#### 3. 根据日志判断问题

##### 情况A：看到"准备提交FormData"但没有"API响应"
**问题**：API请求发出但没有收到响应
- 检查 **Network** 标签页
- 找到 POST `/food/categories/upload` 请求
- 查看 **Status Code**：
  - `200`: 成功，但代码处理有问题
  - `422`: 请求格式错误（FormData问题）
  - `500`: 后端异常
  - 其他：网络问题

##### 情况B：看到"API响应"但是错误对象
**问题**：后端返回了错误
- Console显示的 `result` 对象中有 `msg` 字段
- 例如：`"食物名称 Apple 已存在"`
- 这说明后端校验失败

##### 情况C：没有任何日志输出
**问题**：JavaScript执行出错
- 查看Console中的红色错误信息
- 通常是语法错误或变量未定义

---

## 常见问题及解决方案

### 问题1：API返回422错误
**原因**：FormData格式不正确或表单参数解析失败
**解决**：
1. 检查网络标签中的FormData内容
2. 确认 `name` 字段有值
3. 确认 `nutrition` 如果有值，必须是有效的JSON字符串

### 问题2：API返回"食物名称已存在"
**原因**：数据库中已有同名食物
**解决**：
1. 修改食物名称，添加后缀如"_2"
2. 或登录到数据库删除旧数据

### 问题3：API返回"创建食物类别失败"
**原因**：后端异常，可能是：
- 图片保存失败
- 权限问题
- 磁盘空间不足
**解决**：
1. 检查后端日志：`app.log` 或控制台输出
2. 查看 `/deploy/static/uploads/food_images/` 目录是否存在且可写
3. 查看 `/deploy/static/uploads/` 目录权限

### 问题4：保存成功但列表没有刷新
**原因**：刷新函数执行时机问题
**解决**：
1. 手动刷新页面 F5
2. 如果仍无法看到新增数据，检查后端是否真的创建了数据
   - 查询数据库：`SELECT * FROM food_category ORDER BY created_at DESC LIMIT 1;`

---

## 后端调试

### 启用详细日志
编辑 `app/settings/config.py`：
```python
LOG_LEVEL = "DEBUG"  # 改为 DEBUG
```

### 检查后端日志
```bash
# 查看最后30行日志
tail -30 app.log
```

### 直接测试API
使用 curl 或 Postman 测试：
```bash
curl -X POST http://localhost:8000/food/categories/upload \
  -F "name=TestFood" \
  -F "food_type=Fruit" \
  -F "description=Test Description" \
  -F 'nutrition={"energy": 50, "protein": 1, "fat": 0.2, "carbohydrate": 10, "fiber": 2, "sodium": 5}'
```

---

## 前端调试

### 1. 在handleSave中添加额外日志
编辑 `web/src/views/food/management/index.vue`：
```javascript
const handleSave = async () => {
  console.log('=== 启动保存流程 ===')
  console.log('action:', modalAction.value)
  console.log('form:', modalForm.value)
  // ... 其他代码
}
```

### 2. 检查FormData内容
```javascript
// 在formData构建完成后
for (let [key, value] of formData.entries()) {
  console.log(`${key}:`, value)
}
```

### 3. 拦截API调用
编辑 `web/src/utils/request.js` 或 `request.ts`：
```javascript
// 添加请求拦截器
request.interceptors.request.use(config => {
  if (config.data instanceof FormData) {
    console.log('FormData request:', config.url)
  }
  return config
})

// 添加响应拦截器
request.interceptors.response.use(
  response => {
    if (response.config.url.includes('food')) {
      console.log('Food API response:', response.data)
    }
    return response
  },
  error => {
    console.error('API error:', error.response?.data)
    return Promise.reject(error)
  }
)
```

---

## 数据库调试

### 查看食物类别表
```sql
-- SQLite
SELECT id, name, code, food_type, created_at FROM food_category ORDER BY id DESC LIMIT 10;
```

### 查看营养表
```sql
SELECT n.*, f.name FROM nutrition n 
LEFT JOIN food_category f ON n.food_id = f.id 
ORDER BY n.id DESC LIMIT 10;
```

### 检查是否有错误记录
```sql
SELECT * FROM food_category WHERE name LIKE '%test%';
```

---

## 完整测试流程

1. **清理旧数据**（可选）
   ```sql
   DELETE FROM nutrition WHERE id > 0;
   DELETE FROM food_category WHERE id > 100;
   ```

2. **新增测试食物**
   - 打开浏览器 DevTools Console
   - 新增食物名称：`TestFood_` + 当前时间戳
   - 类型：`Fruit`
   - 不上传图片
   - 仅填营养中的热量字段
   - 点击保存

3. **观察日志**
   - Console应显示多行日志
   - 最关键是 `API响应` 这一行

4. **验证结果**
   - 若成功，页面应显示成功提示并新建项目出现在列表顶部
   - 若失败，显示错误提示并Console中有详细信息

---

## 获取帮助

如果仍然无法解决，请收集以下信息：

1. **浏览器Console输出**（截图或复制文本）
2. **Network标签中的请求/响应**
3. **后端服务器日志**（最后20行）
4. **特定的错误消息**

然后提交问题。
