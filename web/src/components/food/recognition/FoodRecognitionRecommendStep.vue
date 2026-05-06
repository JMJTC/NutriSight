<template>
  <div class="recommend-step">
    <NutritionDashboard
      :current="currentNutrition"
      :food-name-zh="primaryFood.food_name_zh"
      :food-name-en="primaryFood.food_name_en"
      :confidence="primaryFood.confidence"
    />
    <div class="recommend-grid">
      <n-card class="recommend-card" :bordered="false">
        <template #header>
          <div class="section-head"><h3>AI 饮食建议</h3></div>
        </template>
        <div v-if="recommendationLoading" class="loading-wrap">
          <n-spin size="medium" />
          <span class="loading-text">AI 正在生成建议，请稍候...</span>
        </div>
        <n-list v-else :bordered="false">
          <n-list-item v-for="(advice, index) in recommendationTips" :key="index">
            <template #prefix>
              <n-icon color="#10b981" size="20"><CheckmarkCircleOutline /></n-icon>
            </template>
            <span class="advice-text">{{ advice }}</span>
          </n-list-item>
        </n-list>
      </n-card>

      <div class="restart-panel">
        <h4>继续下一次识别</h4>
        <p>重新上传图片，获取新的识别与分析结果。</p>
        <n-button type="primary" ghost @click="$emit('reset')">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          重新开始
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CheckmarkCircleOutline, RefreshOutline } from '@vicons/ionicons5'
import NutritionDashboard from '@/components/food/NutritionDashboard.vue'

defineProps({
  currentNutrition: {
    type: Object,
    default: () => ({}),
  },
  primaryFood: {
    type: Object,
    default: () => ({}),
  },
  recommendationLoading: {
    type: Boolean,
    default: false,
  },
  recommendationTips: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['reset'])
</script>

<style scoped>
.recommend-step {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommend-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
}

.recommend-card {
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
}

.section-head h3 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
  font-weight: 700;
}

.loading-wrap {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.loading-text {
  color: #047857;
  font-size: 14px;
}

.advice-text {
  color: #334155;
  line-height: 1.7;
}

.restart-panel {
  border-radius: 12px;
  padding: 20px;
  color: #ffffff;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
}

.restart-panel h4 {
  margin: 0;
  font-size: 20px;
}

.restart-panel p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

@media (max-width: 1024px) {
  .recommend-grid {
    grid-template-columns: 1fr;
  }
}
</style>
