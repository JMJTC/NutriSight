<template>
  <n-card class="dashboard-card shadow-2xl border-0 bg-white rounded-[50px] overflow-visible">
    <template #header>
      <div class="flex items-center space-x-5 px-4">
        <span class="w-3 h-12 bg-emerald-500 rounded-full"></span>
        <h3 class="text-5xl font-black text-slate-900 tracking-tighter">个性化营养目标仪表盘</h3>
      </div>
    </template>
    <template #header-extra>
      <n-button quaternary circle class="hover:bg-emerald-50 transition-colors w-16 h-16">
        <template #icon>
          <n-icon size="36" color="#64748b"><SettingsOutline /></n-icon>
        </template>
      </n-button>
    </template>
    
    <div class="px-10 py-8">
      <n-grid :cols="4" :x-gap="48" :y-gap="48">
        <n-grid-item v-for="(goal, key) in goals" :key="key">
          <n-card class="!bg-slate-50/50 !border-2 !border-slate-100 rounded-[40px] hover:shadow-xl transition-all cursor-default p-6">
            <n-statistic :label="goal.label" class="!text-3xl font-black">
              <template #prefix>
                <div class="p-5 rounded-[30px] bg-white shadow-md mr-6 border-2 border-slate-100">
                  <n-icon :color="goal.color" size="64">
                    <component :is="goal.icon" />
                  </n-icon>
                </div>
              </template>
              <div class="flex flex-col mt-8">
                <div class="flex items-baseline justify-between mb-4">
                  <span class="text-5xl font-black text-slate-900 tracking-tighter">{{ current[key] }}</span>
                  <span class="text-2xl font-bold text-slate-400">/ {{ goal.target }} {{ goal.unit }}</span>
                </div>
                <n-progress
                  type="line"
                  :percentage="Math.min(100, (current[key] / goal.target) * 100)"
                  :color="goal.color"
                  :show-indicator="false"
                  processing
                  height="24"
                  class="rounded-full overflow-hidden border-2 border-white shadow-inner"
                />
              </div>
            </n-statistic>
          </n-card>
        </n-grid-item>
      </n-grid>
      
      <n-divider class="!my-16" />
      
      <div class="summary-tips p-12 rounded-[40px] bg-gradient-to-r from-emerald-500 to-emerald-700 text-white shadow-2xl shadow-emerald-200/50 flex items-center min-h-[180px]">
        <div class="bg-white/20 p-6 rounded-[30px] mr-12 backdrop-blur-xl border-2 border-white/30 shadow-lg">
          <n-icon size="72" class="text-white"><InformationCircleOutline /></n-icon>
        </div>
        <div class="flex-grow">
          <h4 class="font-black text-4xl mb-4 tracking-tight">今日膳食 AI 专家点评</h4>
          <p class="text-3xl font-bold opacity-95 leading-relaxed max-w-[1200px]">
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
  InformationCircleOutline
} from '@vicons/ionicons5'

const props = defineProps({
  current: {
    type: Object,
    default: () => ({
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0
    })
  }
})

const goals = {
  calories: { label: '能量消耗 (Energy)', target: 2000, unit: 'kcal', color: '#00A896', icon: FlashOutline },
  protein: { label: '蛋白质 (Protein)', target: 60, unit: 'g', color: '#02C39A', icon: LeafOutline },
  carbs: { label: '碳水 (Carbs)', target: 250, unit: 'g', color: '#FFE66D', icon: FlameOutline },
  fat: { label: '脂肪 (Fat)', target: 65, unit: 'g', color: '#2080F0', icon: WaterOutline }
}

const analysisSummary = computed(() => {
  const calPercent = (props.current.calories / goals.calories.target) * 100
  if (calPercent > 80) return "今天的热量摄入已经接近目标，建议晚餐清淡一些。"
  if (calPercent > 40) return "目前的营养摄入较为均衡，保持良好的饮食习惯。"
  return "今日营养摄入还不足，建议多摄入一些优质蛋白和新鲜蔬菜。"
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
