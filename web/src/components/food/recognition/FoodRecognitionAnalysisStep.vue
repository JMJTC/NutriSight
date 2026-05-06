<template>
  <div class="analysis-step">
    <div class="section-head">
      <h3>营养可视化分析</h3>
    </div>
    <n-grid :cols="2" :x-gap="16" :y-gap="16">
      <n-grid-item>
        <n-card title="识别置信度" class="chart-card" :bordered="false">
          <ConfidenceHeatmap :data="safeDetails" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card title="营养素结构" class="chart-card" :bordered="false">
          <NutritionRadarChart :data="safeDetails" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <div class="action-row mt-4">
      <n-button quaternary @click="$emit('back')">
        <template #icon>
          <n-icon><ArrowBackOutline /></n-icon>
        </template>
        返回识别结果
      </n-button>
      <n-button type="primary" @click="$emit('recommend')">
        生成饮食建议
        <template #icon>
          <n-icon><ArrowForwardOutline /></n-icon>
        </template>
      </n-button>
    </div>
    <div class="step-fallback-action">
      <n-button type="default" @click="$emit('recommend')">图表异常时直接查看建议</n-button>
    </div>
  </div>
</template>

<script setup>
import { ArrowBackOutline, ArrowForwardOutline } from '@vicons/ionicons5'
import ConfidenceHeatmap from '@/components/food/ConfidenceHeatmap.vue'
import NutritionRadarChart from '@/components/food/NutritionRadarChart.vue'

defineProps({
  safeDetails: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['back', 'recommend'])
</script>

<style scoped>
.analysis-step {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-head h3 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
  font-weight: 700;
}

.chart-card {
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
}

.action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.step-fallback-action {
  margin-top: 4px;
  display: flex;
  justify-content: flex-end;
}
</style>
