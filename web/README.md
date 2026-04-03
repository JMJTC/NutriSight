# 食智眸 - 前端项目 (Vue3 + Naive UI)

这是 **食智眸 (Smart Food Eye)** 的前端部分，基于 Vue 3、Vite 和 Naive UI 构建。

## 🚀 快速开始

### 1. 安装依赖
推荐使用 [pnpm](https://pnpm.io/) 管理依赖。

```bash
# 安装 pnpm (如果尚未安装)
npm i -g pnpm

# 安装项目依赖
pnpm install
```

### 2. 环境变量配置
在 `.env.development` 中配置后端接口地址：

```text
VITE_BASE_API = '/api/v1'
VITE_USE_PROXY = true
```

### 3. 本地开发
启动开发服务器：

```bash
pnpm dev
```
启动后访问：`http://localhost:3100`

### 4. 生产构建
构建打包文件：

```bash
pnpm build
```

## 🛠️ 技术栈
- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI 组件库**: Naive UI
- **状态管理**: Pinia
- **路由**: Vue Router
- **样式**: UnoCSS + SASS
- **图表**: ECharts + Vue-ECharts
- **代码规范**: ESLint + Prettier

## 📂 目录结构
- `src/api`: 后端接口封装
- `src/components`: 公用组件
- `src/layout`: 页面布局
- `src/store`: 状态管理 (Pinia modules)
- `src/views`: 业务页面 (包含食物识别、系统管理等)
- `src/utils`: 工具函数 (Axios 拦截器、Token 管理等)
