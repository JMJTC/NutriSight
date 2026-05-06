<template>
  <div class="recognition-step">
    <div class="preview-panel">
      <img
        :src="getImageUrl(result?.annotated_image_path || result?.image_path)"
        class="preview-image"
        alt="识别标注图"
      />
    </div>
    <div class="result-panel">
      <div class="panel-title">
        <h3>识别结果</h3>
        <div class="panel-title-actions">
          <n-tag type="success" round>{{ result?.details?.length || 0 }} 项</n-tag>
          <n-button type="primary" size="small" @click="$emit('go-analysis')">进入分析</n-button>
        </div>
      </div>

      <n-scrollbar class="result-list-scroll">
        <div class="result-list">
          <div v-for="(item, index) in mappedDetails" :key="index" class="result-item">
            <div class="flex items-center justify-between gap-2">
              <div class="food-name-wrap">
                <div class="food-name-zh">{{ item.food_name_zh }}</div>
                <div class="food-name-en">{{ item.food_name_en }}</div>
              </div>
              <div class="flex items-center gap-2">
                <n-tag
                  v-if="primaryDetail && item.class_id === primaryDetail.class_id"
                  size="small"
                  type="warning"
                  :bordered="false"
                >
                  最高
                </n-tag>
                <n-tag size="small" type="success" :bordered="false">
                  {{ (item.confidence * 100).toFixed(1) }}%
                </n-tag>
              </div>
            </div>
            <div class="food-meta">
              <n-icon size="16"><FlameOutline /></n-icon>
              <span>{{ item.nutrition.calories }} kcal / 100g</span>
            </div>
          </div>
        </div>
      </n-scrollbar>

      <n-button type="primary" block class="go-analysis-btn" @click="$emit('go-analysis')">
        查看营养分析
        <template #icon>
          <n-icon><ArrowForwardOutline /></n-icon>
        </template>
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ArrowForwardOutline, FlameOutline } from '@vicons/ionicons5'

defineProps({
  getImageUrl: {
    type: Function,
    required: true,
  },
  mappedDetails: {
    type: Array,
    default: () => [],
  },
  primaryDetail: {
    type: Object,
    default: null,
  },
  result: {
    type: Object,
    default: null,
  },
})

defineEmits(['go-analysis'])
</script>

<style scoped>
.recognition-step {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
}

.preview-panel,
.result-panel {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
}

.preview-panel {
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  width: 100%;
  max-height: 520px;
  border-radius: 10px;
  object-fit: contain;
  background: #fff;
}

.panel-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.panel-title-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-title h3 {
  margin: 0;
  font-size: 18px;
  color: #0f172a;
}

.result-panel {
  min-height: 500px;
  display: flex;
  flex-direction: column;
}

.result-list-scroll {
  flex: 1;
  min-height: 260px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px;
}

.food-name-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.food-name-zh {
  font-size: 15px;
  color: #0f172a;
  font-weight: 700;
  line-height: 1.2;
}

.food-name-en {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
  line-height: 1.2;
}

.food-meta {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.go-analysis-btn {
  margin-top: 12px;
}

@media (max-width: 1024px) {
  .recognition-step {
    grid-template-columns: 1fr;
  }
}
</style>
