<template>
  <n-card class="dashboard-card overflow-visible border-0 rounded-[50px] bg-white shadow-2xl">
    <template #header>
      <div class="flex items-center px-4 space-x-5">
        <span class="h-12 w-3 rounded-full bg-emerald-500"></span>
        <div class="flex flex-col">
          <h3 class="text-5xl font-black tracking-tighter text-slate-900">个性化营养目标仪表盘</h3>
          <div v-if="foodNameZh || foodNameEn" class="mt-2 flex items-baseline gap-3">
            <span v-if="foodNameZh" class="text-2xl font-black text-slate-700">{{ foodNameZh }}</span>
            <span v-if="foodNameEn" class="text-xl font-bold text-slate-400">{{ foodNameEn }}</span>
            <span v-if="confidencePercent !== ''" class="text-xl font-bold text-emerald-600"
              >{{ confidencePercent }}</span
            >
          </div>
        </div>
      </div>
    </template>
    <template #header-extra>
      <n-button quaternary circle class="h-16 w-16 transition-colors hover:bg-emerald-50">
        <template #icon>
          <n-icon size="36" color="#64748b"><SettingsOutline /></n-icon>
        </template>
      </n-button>
    </template>

    <div class="px-10 py-8">
      <n-grid :cols="3" :x-gap="48" :y-gap="48">
        <n-grid-item v-for="(goal, key) in goals" :key="key">
          <n-card
            class="cursor-default rounded-[40px] p-6 transition-all !border-2 !border-slate-100 !bg-slate-50/50 hover:shadow-xl"
          >
            <n-statistic :label="goal.label" class="font-black !text-3xl">
              <template #prefix>
                <div class="mr-6 border-2 border-slate-100 rounded-[30px] bg-white p-5 shadow-md">
                  <n-icon :color="goal.color" size="64">
                    <component :is="goal.icon" />
                  </n-icon>
                </div>
              </template>
              <div class="mt-8 flex flex-col">
                <div class="mb-4 flex items-baseline justify-between">
                  <span class="text-5xl font-black tracking-tighter text-slate-900">{{
                    formatValue(current[key], goal.precision)
                  }}</span>
                  <span class="text-2xl font-bold text-slate-400"
                    >/ {{ goal.target }} {{ goal.unit }}</span
                  >
                </div>
                <n-progress
                  type="line"
                  :percentage="
                    Math.min(100, ((Number(current[key]) || 0) / (goal.target || 1)) * 100)
                  "
                  :color="goal.color"
                  :show-indicator="false"
                  processing
                  height="24"
                  class="overflow-hidden border-2 border-white rounded-full shadow-inner"
                />
              </div>
            </n-statistic>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-divider class="!my-16" />

      <div
        class="summary-tips min-h-[180px] flex items-center rounded-[40px] from-emerald-500 to-emerald-700 bg-gradient-to-r p-12 text-white shadow-2xl shadow-emerald-200/50"
      >
        <div
          class="mr-12 border-2 border-white/30 rounded-[30px] bg-white/20 p-6 shadow-lg backdrop-blur-xl"
        >
          <n-icon size="72" class="text-white"><InformationCircleOutline /></n-icon>
        </div>
        <div class="flex-grow">
          <h4 class="mb-4 text-4xl font-black tracking-tight">今日膳食 AI 专家点评</h4>
          <p class="max-w-[1200px] text-3xl font-bold leading-relaxed opacity-95">
            {{ analysisSummary }}
          </p>
        </div>
      </div>
    </div>
  </n-card>
</template>

<script setup>
import { computed } from 'vue'
import {
  FlashOutline,
  LeafOutline,
  FlameOutline,
  WaterOutline,
  SettingsOutline,
  InformationCircleOutline,
} from '@vicons/ionicons5'
import { useUserStore } from '@/store'

const props = defineProps({
  current: {
    type: Object,
    default: () => ({
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0,
      fiber: 0,
      sodium: 0,
    }),
  },
  foodNameZh: {
    type: String,
    default: '',
  },
  foodNameEn: {
    type: String,
    default: '',
  },
  confidence: {
    type: Number,
    default: null,
  },
})

const userStore = useUserStore()

const targets = computed(() => {
  const heightCm = Number(userStore.userInfo?.height_cm)
  const weightKg = Number(userStore.userInfo?.weight_kg)
  const gender = Number(userStore.userInfo?.gender)
  const age = Number(userStore.userInfo?.age)

  const hasProfile =
    Number.isFinite(heightCm) &&
    Number.isFinite(weightKg) &&
    Number.isFinite(gender) &&
    Number.isFinite(age)
  if (!hasProfile) {
    return { calories: 2000, protein: 60, carbs: 250, fat: 65, fiber: 25, sodium: 2000 }
  }

  let bmr = 0
  if (gender === 1) bmr = 10 * weightKg + 6.25 * heightCm - 5 * age + 5
  else if (gender === 2) bmr = 10 * weightKg + 6.25 * heightCm - 5 * age - 161
  else bmr = 10 * weightKg + 6.25 * heightCm - 5 * age - 78

  const totalCalories = Math.round(bmr * 1.375)
  const proteinG = Math.round((totalCalories * 0.15) / 4)
  const fatG = Math.round((totalCalories * 0.25) / 9)
  const carbsG = Math.round((totalCalories * 0.6) / 4)

  const fiberG = gender === 2 ? 21 : 25
  const sodiumMg = 2000

  return {
    calories: totalCalories,
    protein: proteinG,
    carbs: carbsG,
    fat: fatG,
    fiber: fiberG,
    sodium: sodiumMg,
  }
})

const goals = computed(() => ({
  calories: {
    label: '能量 (Energy)',
    target: targets.value.calories,
    unit: 'kcal',
    precision: 0,
    color: '#00A896',
    icon: FlashOutline,
  },
  protein: {
    label: '蛋白质 (Protein)',
    target: targets.value.protein,
    unit: 'g',
    precision: 1,
    color: '#02C39A',
    icon: LeafOutline,
  },
  carbs: {
    label: '碳水 (Carbs)',
    target: targets.value.carbs,
    unit: 'g',
    precision: 1,
    color: '#FFE66D',
    icon: FlameOutline,
  },
  fat: {
    label: '脂肪 (Fat)',
    target: targets.value.fat,
    unit: 'g',
    precision: 1,
    color: '#2080F0',
    icon: WaterOutline,
  },
  fiber: {
    label: '膳食纤维 (Fiber)',
    target: targets.value.fiber,
    unit: 'g',
    precision: 1,
    color: '#7C3AED',
    icon: LeafOutline,
  },
  sodium: {
    label: '钠 (Sodium)',
    target: targets.value.sodium,
    unit: 'mg',
    precision: 0,
    color: '#F97316',
    icon: WaterOutline,
  },
}))

const formatValue = (val, precision = 0) => {
  const num = Number(val)
  if (!Number.isFinite(num)) return 0
  return precision > 0 ? num.toFixed(precision) : Math.round(num)
}

const analysisSummary = computed(() => {
  const calTarget = goals.value.calories.target || 1
  const calPercent = (Number(props.current.calories) / calTarget) * 100
  if (calPercent > 80) return '今天的热量摄入已经接近目标，建议晚餐清淡一些。'
  if (calPercent > 40) return '目前的营养摄入较为均衡，保持良好的饮食习惯。'
  return '今日营养摄入还不足，建议多摄入一些优质蛋白和新鲜蔬菜。'
})

const confidencePercent = computed(() => {
  const v = props.confidence
  if (!Number.isFinite(v)) return ''
  return `${(v * 100).toFixed(1)}%`
})
</script>

<style scoped>
.dashboard-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.dashboard-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 168, 150, 0.1), 0 4px 6px -2px rgba(0, 168, 150, 0.05);
}
.mr-2 {
  margin-right: 0.5rem;
}
.mt-2 {
  margin-top: 0.5rem;
}
.mb-2 {
  margin-bottom: 0.5rem;
}
</style>
