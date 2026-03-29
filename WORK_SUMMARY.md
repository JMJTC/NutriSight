# 迭代总结（截至 2026-03-10）

## 1）完成了哪些功能

- 食物识别：前端上传图片到 `api/food/recognize`，后端保存原图并调用 YOLO 推理
- 识别结果：后端返回 `record_id`、`image_path`、`annotated_image_path`、`details`、`nutrition`、`created_at`
- 标注图片：YOLO 预测后用 Pillow 画框并保存到 `deploy/static/uploads`，返回 `annotated_image_path`
- 持久化：识别记录存入 `RecognitionRecord`，详情 `RecognitionDetail`，营养 `NutritionAnalysis`
- 历史记录：`food/history` 返回记录列表，`food/record/{id}` 返回详情
- 前端显示：`recognition/index.vue` 显示识别图和营养信息，`history/index.vue` 显示缩略图及详情弹窗
- 图片显示优化：CSS 新增 `max-height` + `overflow: auto`，确保长图可滚动查看
- 静态文件配置：`app/__init__.py` 加 `app.mount('/static', StaticFiles(directory=<BASE_DIR>/deploy/static), name='static')`
- 调试增强：前端添加调试面板，记录 `image_path`/`annotated_image_path`/URL，并支持 `onImageError`

## 2）使用了哪些技术方案

- 后端：FastAPI + Tortoise ORM + SQLite
- 数据迁移：aerich（遇到 sqlite comment 不支持，采用手动 ALTER TABLE）
- 模型：Ultralytics YOLO、Pillow (ImageDraw)
- 前端：Vue3 + Naive UI + Vite + Axios（封装在 `utils/http`）
- 代理：`vite.config.js` 配置 `/api/v1` 转发到 `http://127.0.0.1:9999`
- 静态资源：FastAPI StaticFiles 挂载，URL：`http://127.0.0.1:9999/static/uploads/...`
- 调试：在前端增加 `console.log('Recognition result:', result)` 和路径信息展示

## 3）待解决问题

- YOLO 在某些图片检测失败（预测 `predictions` 为空），`annotated_image_path` 为空
- 前端 `识别成功` 后有时提示 `请求出错`（可能是 Spinner/状态流或拦截器处理）
- 数据库迁移：`aerich` 对 SQLite 进行字段 comment 变更异常，需要手动迁移脚本
- 历史记录图未展示：需继续确认 `history`接口返回内容是否包含 `annotated_image_path`，以及 URL 构造是否正确
- 网络问题：检测 `http://127.0.0.1:9999/static/uploads/<file>` 能否访问，一旦不能需要早期联网、代理或路径修正

