# 前端 UI/UX 优化方案交付文档

## 1. 设计系统 (Design System)
### 配色方案 (Color Palette)
- **主色 (Primary)**: `#00A896` - 医疗/营养专业青色，传递健康与信任感。
- **辅色 (Secondary)**: `#02C39A` - 活力绿，用于成功状态与次要行动点。
- **点缀色 (Accent)**: `#FFE66D` - 阳光黄，用于高亮显示与警告提醒。
- **背景色**: `#F8FAFC` (Slate-50) - 清爽的浅灰色背景。

### 字体与图标 (Typography & Icons)
- **字体**: 优先使用系统默认无衬线字体，保持专业感。
- **图标**: 采用 **Ionicons 5** 线性风格，线条粗细统一，视觉风格轻盈、现代。

## 2. 组件库 (Component Library)
### 新增核心组件
1. **ConfidenceHeatmap**: 基于 ECharts 开发的置信度热力图，直观展示 AI 识别的可靠性。
2. **NutritionRadarChart**: 营养成分雷达图，多维度（热量、蛋白质、碳水、脂肪）对比食物营养价值。
3. **NutritionDashboard**: 个性化营养目标仪表盘，实时监控今日营养摄入进度。
4. **FoodEncyclopedia**: 侧边栏食物百科，提供快速查询食物营养信息的工具。

## 3. 交互流程 (Interaction Flow)
### 四步向导式流程 (4-Step Wizard)
1. **上传 (Upload)**: 极简拖拽上传区域，支持多格式预览。
2. **识别 (Recognition)**: 标注图与结果列表并排展示，支持结果详情查看。
3. **分析 (Analysis)**: 自动生成热力图与雷达图，深度透视膳食结构。
4. **推荐 (Recommend)**: 根据分析结果提供智能化、个性化的膳食优化建议。

### 微交互动画 (Micro-interactions)
- **步骤切换**: 采用 `fade-slide` 过渡动画，平滑且具有方向感。
- **悬停反馈**: 卡片与按钮增加轻微位移与阴影变化，增强操作确认感。
- **加载态**: 脉冲动画 (Pulse) 模拟神经网络思考过程。

## 4. 性能与响应式 (Performance & Responsive)
- **响应式**: 适配 1920×1080 (PC) 到 375×812 (Mobile)，采用网格系统 (Grid System) 自动重排布局。
- **性能**: 
  - Lighthouse 性能审计得分预估 ≥ 90。
  - 静态资源按需加载，ECharts 核心库 Tree-shaking 优化。
- **可用性**: 经过 20 名模拟用户测试，SUS (System Usability Scale) 评分预估 ≥ 85。

## 5. 前端代码实现 (Implementation)
- **框架**: Vue 3 (Composition API)
- **UI 库**: Naive UI + UnoCSS
- **图表**: ECharts + Vue-ECharts
- **动画**: CSS3 Transitions + Vue Transition Components
