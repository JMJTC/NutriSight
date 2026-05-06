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
            <FoodRecognitionUploadStep
              v-if="currentStep === 1"
              :loading="loading"
              :custom-request="handleUpload"
              @camera-select="uploadByRawFile"
              @remove="onRemove"
            />

            <FoodRecognitionResultStep
              v-else-if="currentStep === 2"
              :result="result"
              :mapped-details="mappedDetails"
              :primary-detail="primaryDetail"
              :get-image-url="getImageUrl"
              @go-analysis="goToStep(3)"
            />

            <FoodRecognitionAnalysisStep
              v-else-if="currentStep === 3"
              :safe-details="safeDetails"
              @back="goToStep(2)"
              @recommend="goToStep(4)"
            />

            <FoodRecognitionRecommendStep
              v-else-if="currentStep === 4"
              :current-nutrition="currentNutrition"
              :primary-food="primaryFood"
              :recommendation-loading="recommendationLoading"
              :recommendation-tips="recommendationTips"
              @reset="resetWizard"
            />
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
import { RestaurantOutline } from '@vicons/ionicons5'
import FoodEncyclopedia from '@/components/food/FoodEncyclopedia.vue'
import NutritionDashboard from '@/components/food/NutritionDashboard.vue'
import FoodRecognitionAnalysisStep from '@/components/food/recognition/FoodRecognitionAnalysisStep.vue'
import FoodRecognitionRecommendStep from '@/components/food/recognition/FoodRecognitionRecommendStep.vue'
import FoodRecognitionResultStep from '@/components/food/recognition/FoodRecognitionResultStep.vue'
import FoodRecognitionUploadStep from '@/components/food/recognition/FoodRecognitionUploadStep.vue'
import { useFoodRecognition } from './useFoodRecognition'

const {
  currentNutrition,
  currentStep,
  getImageUrl,
  goToStep,
  handleUpload,
  loading,
  mappedDetails,
  onRemove,
  primaryDetail,
  primaryFood,
  recommendationLoading,
  recommendationTips,
  resetWizard,
  result,
  safeDetails,
  showEncyclopedia,
  stepStatus,
  uploadByRawFile,
} = useFoodRecognition()
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
</style>
