<template>
  <div class="food-recognition-container min-h-screen">
    <div class="mx-auto max-w-[1280px] w-full px-4 py-6 lg:px-8 md:px-6">
      <div class="page-header mb-6">
        <div>
          <h1 class="title flex items-center gap-3">
            <n-icon size="34" color="#10b981"><RestaurantOutline /></n-icon>
            食物识别分析
          </h1>
          <p class="subtitle mt-2">上传图片，一键完成识别、营养分析与饮食建议。</p>
        </div>
        <!-- <n-button
          type="primary"
          round
          tertiary
          class="encyclopedia-btn"
          @click="showEncyclopedia = true"
        >
          <template #icon>
            <n-icon><BookOutline /></n-icon>
          </template>
          食物百科
        </n-button> -->
      </div>

      <n-card class="wizard-card" :bordered="false">
        <n-steps :current="currentStep" :status="stepStatus" class="steps-bar" size="small">
          <n-step title="上传" description="选择图片" />
          <n-step title="识别" description="查看结果" />
          <n-step title="分析" description="营养图表" />
          <n-step title="建议" description="健康指导" />
        </n-steps>

        <transition name="fade-slide" mode="out-in">
          <div :key="currentStep" class="step-content mt-6">
            <div v-if="currentStep === 1" class="upload-step">
              <n-upload
                directory-dnd
                multiple
                action="#"
                :custom-request="handleUpload"
                :max="1"
                accept="image/*"
                @remove="onRemove"
              >
                <n-upload-dragger class="upload-dragger-custom">
                  <div class="upload-dragger-inner">
                    <n-icon size="56" color="#10b981">
                      <CloudUploadOutline />
                    </n-icon>
                    <h3 class="upload-title mt-4">点击或拖拽上传食物图片</h3>
                    <p class="upload-desc mt-2">支持 JPG / PNG / WEBP，识别后自动进入下一步</p>
                    <div class="mt-4 flex flex-wrap justify-center gap-2">
                      <n-tag type="success" round>高精度识别</n-tag>
                      <n-tag type="info" round>营养分析</n-tag>
                      <n-tag type="warning" round>饮食建议</n-tag>
                    </div>
                  </div>
                </n-upload-dragger>
              </n-upload>

              <div v-if="loading" class="loading-wrap">
                <n-spin size="medium" />
                <span class="loading-text">AI 正在分析图片，请稍候...</span>
              </div>
            </div>

            <div v-else-if="currentStep === 2" class="recognition-step">
              <div class="preview-panel">
                <img
                  :src="getImageUrl(result.annotated_image_path || result.image_path)"
                  class="preview-image"
                  alt="识别标注图"
                />
              </div>
              <div class="result-panel">
                <div class="panel-title">
                  <h3>识别结果</h3>
                  <div class="panel-title-actions">
                    <n-tag type="success" round>{{ result.details.length }} 项</n-tag>
                    <n-button type="primary" size="small" @click="goToStep(3)"> 进入分析 </n-button>
                  </div>
                </div>

                <n-scrollbar class="result-list-scroll">
                  <div class="result-list">
                    <div v-for="(item, index) in safeDetails" :key="index" class="result-item">
                      <div class="flex items-center justify-between gap-2">
                        <div class="food-name-wrap">
                          <div class="food-name-zh">{{ item.food_name_zh }}</div>
                          <div class="food-name-en">{{ item.food_name_en }}</div>
                        </div>
                        <n-tag size="small" type="success" :bordered="false">
                          {{ (item.confidence * 100).toFixed(1) }}%
                        </n-tag>
                      </div>
                      <div class="food-meta">
                        <n-icon size="16"><FlameOutline /></n-icon>
                        <span>{{ item.nutrition.calories }} kcal / 100g</span>
                      </div>
                    </div>
                  </div>
                </n-scrollbar>

                <n-button type="primary" block class="go-analysis-btn" @click="goToStep(3)">
                  查看营养分析
                  <template #icon
                    ><n-icon><ArrowForwardOutline /></n-icon
                  ></template>
                </n-button>
              </div>
            </div>

            <div v-else-if="currentStep === 3" class="analysis-step">
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
                <n-button quaternary @click="goToStep(2)">
                  <template #icon
                    ><n-icon><ArrowBackOutline /></n-icon
                  ></template>
                  返回识别结果
                </n-button>
                <n-button type="primary" @click="goToStep(4)">
                  生成饮食建议
                  <template #icon
                    ><n-icon><ArrowForwardOutline /></n-icon
                  ></template>
                </n-button>
              </div>
              <div class="step-fallback-action">
                <n-button type="default" @click="goToStep(4)">图表异常时直接查看建议</n-button>
              </div>
            </div>

            <div v-else-if="currentStep === 4" class="recommend-step">
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
                  <n-button type="primary" ghost @click="resetWizard">
                    <template #icon
                      ><n-icon><RefreshOutline /></n-icon
                    ></template>
                    重新开始
                  </n-button>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </n-card>

      <div v-if="result && currentStep !== 4" class="mt-6 animate-fade-in">
        <NutritionDashboard
          :current="currentNutrition"
          :food-name-zh="primaryFood.food_name_zh"
          :food-name-en="primaryFood.food_name_en"
          :confidence="primaryFood.confidence"
        />
      </div>
    </div>

    <FoodEncyclopedia v-model:visible="showEncyclopedia" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  CloudUploadOutline,
  RestaurantOutline,
  BookOutline,
  ArrowForwardOutline,
  ArrowBackOutline,
  CheckmarkCircleOutline,
  RefreshOutline,
  FlameOutline,
} from '@vicons/ionicons5'
import { useMessage } from 'naive-ui'
import api from '@/api'
import ConfidenceHeatmap from '@/components/food/ConfidenceHeatmap.vue'
import NutritionRadarChart from '@/components/food/NutritionRadarChart.vue'
import FoodEncyclopedia from '@/components/food/FoodEncyclopedia.vue'
import NutritionDashboard from '@/components/food/NutritionDashboard.vue'

const message = useMessage()
const loading = ref(false)
const result = ref(null)
const currentStep = ref(1)
const stepStatus = ref('process')
const showEncyclopedia = ref(false)

const mappedDetails = computed(() => {
  const details = Array.isArray(result.value?.details) ? result.value.details : []
  return details.map((item, index) => {
    const nutrition = item?.nutrition || {}
    const foodNameZh = item?.food_name_zh || item?.food_name || `食物${index + 1}`
    const foodNameEn = item?.food_name_en || item?.food_name || foodNameZh
    return {
      food_name: foodNameZh,
      food_name_zh: foodNameZh,
      food_name_en: foodNameEn,
      confidence: Number(item?.confidence) || 0,
      nutrition: {
        calories: Number(nutrition.calories) || 0,
        protein: Number(nutrition.protein) || 0,
        carbs: Number(nutrition.carbs) || 0,
        fat: Number(nutrition.fat) || 0,
        fiber: Number(nutrition.fiber) || 0,
        sodium: Number(nutrition.sodium) || 0,
      },
    }
  })
})

const primaryDetail = computed(() => {
  const list = mappedDetails.value
  if (!list.length) return null
  return list.reduce((best, cur) => (cur.confidence > best.confidence ? cur : best), list[0])
})

const safeDetails = computed(() => {
  const best = primaryDetail.value
  return best ? [best] : []
})

const currentNutrition = computed(() => {
  const best = primaryDetail.value
  if (!best) return { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0, sodium: 0 }
  return {
    calories: Number(best.nutrition?.calories) || 0,
    protein: Number(best.nutrition?.protein) || 0,
    carbs: Number(best.nutrition?.carbs) || 0,
    fat: Number(best.nutrition?.fat) || 0,
    fiber: Number(best.nutrition?.fiber) || 0,
    sodium: Number(best.nutrition?.sodium) || 0,
  }
})

const primaryFood = computed(() => {
  const best = primaryDetail.value
  if (!best) return { food_name_zh: '', food_name_en: '', confidence: null }
  return {
    food_name_zh: best.food_name_zh || '',
    food_name_en: best.food_name_en || '',
    confidence: Number.isFinite(best.confidence) ? best.confidence : null,
  }
})

const recommendationTips = ref([])
const recommendationLoading = ref(false)

const loadRecommendation = async () => {
  if (!result.value?.record_id) return
  if (recommendationLoading.value) return
  recommendationLoading.value = true
  try {
    const res = await api.generateFoodRecordRecommendation(result.value.record_id)
    if (res.code === 200) {
      recommendationTips.value = Array.isArray(res.data?.tips) ? res.data.tips : []
    } else {
      recommendationTips.value = []
      message.error(res.msg || '生成建议失败')
    }
  } catch (error) {
    recommendationTips.value = []
    message.error('生成建议请求出错')
  } finally {
    recommendationLoading.value = false
  }
}

const handleUpload = async ({ file, onFinish, onError }) => {
  loading.value = true
  result.value = null
  recommendationTips.value = []

  const formData = new FormData()
  formData.append('file', file.file)

  try {
    const res = await api.recognizeFood(formData)
    if (res.code === 200) {
      result.value = res.data
      recommendationTips.value = []
      message.success('识别成功 (Recognized Successfully)')
      currentStep.value = 2
      onFinish()
    } else {
      message.error(res.msg || '识别失败')
      onError()
    }
  } catch (error) {
    message.error('请求出错')
    onError()
  } finally {
    loading.value = false
  }
}

const onRemove = () => {
  result.value = null
  currentStep.value = 1
  recommendationTips.value = []
}

const resetWizard = () => {
  result.value = null
  currentStep.value = 1
  recommendationTips.value = []
}

const goToStep = (step) => {
  if (!result.value && step > 1) {
    currentStep.value = 1
    return
  }
  if (step === 3 && safeDetails.value.length === 0) {
    message.warning('暂无可分析的识别结果')
    return
  }
  if (step === 4) {
    loadRecommendation()
  }
  currentStep.value = step
}

const getImageUrl = (path) => {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  const backendHost = import.meta.env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:9999'
  return `${backendHost}${path}`
}
</script>

<style scoped>
.food-recognition-container {
  overflow-y: auto;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
}

.subtitle {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

.encyclopedia-btn {
  height: 38px;
}

.wizard-card {
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.steps-bar {
  padding: 4px 2px 0;
}

.step-content {
  min-height: 460px;
}

.upload-step {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.upload-dragger-custom {
  border: 2px dashed #86efac !important;
  border-radius: 14px !important;
  background: #f8fffc !important;
  transition: all 0.2s ease;
}

.upload-dragger-custom:hover {
  border-color: #10b981 !important;
  box-shadow: 0 6px 18px rgba(16, 185, 129, 0.15);
}

.upload-dragger-inner {
  min-height: 270px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

.upload-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}

.upload-desc {
  margin: 0;
  color: #64748b;
  font-size: 14px;
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

.food-name {
  font-size: 15px;
  color: #0f172a;
  font-weight: 600;
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

.analysis-step,
.recommend-step {
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

.recommend-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
}

.recommend-card {
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
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

.animate-fade-in {
  animation: fadeIn 0.35s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 1024px) {
  .recognition-step,
  .recommend-grid {
    grid-template-columns: 1fr;
  }
}
</style>
