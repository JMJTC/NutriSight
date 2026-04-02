<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup>
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { ref, watch } from 'vue'

use([
  CanvasRenderer,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
])

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
})

const option = ref({})

const updateChart = () => {
  const foodDetails = props.data

  const radarData = foodDetails.map((item) => ({
    name: item.food_name,
    value: [
      item.nutrition.calories,
      item.nutrition.protein,
      item.nutrition.carbs,
      item.nutrition.fat,
    ],
  }))

  const maxValues = {
    calories: Math.max(...foodDetails.map((item) => item.nutrition.calories), 100),
    protein: Math.max(...foodDetails.map((item) => item.nutrition.protein), 10),
    carbs: Math.max(...foodDetails.map((item) => item.nutrition.carbs), 50),
    fat: Math.max(...foodDetails.map((item) => item.nutrition.fat), 10),
  }

  option.value = {
    title: {
      text: '营养分布雷达图 (Nutrition Radar)',
      left: 'center',
      textStyle: {
        color: '#00A896',
        fontSize: 14,
      },
    },
    tooltip: {
      trigger: 'item',
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'middle',
      data: foodDetails.map((item) => item.food_name),
    },
    radar: {
      indicator: [
        { name: '热量 (kcal)', max: maxValues.calories },
        { name: '蛋白质 (g)', max: maxValues.protein },
        { name: '碳水 (g)', max: maxValues.carbs },
        { name: '脂肪 (g)', max: maxValues.fat },
      ],
      shape: 'circle',
      splitNumber: 5,
      axisName: {
        color: '#00A896',
      },
      splitLine: {
        lineStyle: {
          color: ['rgba(0, 168, 150, 0.1)', 'rgba(0, 168, 150, 0.2)', 'rgba(0, 168, 150, 0.4)', 'rgba(0, 168, 150, 0.6)', 'rgba(0, 168, 150, 0.8)'],
        },
      },
      splitArea: {
        show: false,
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 168, 150, 0.5)',
        },
      },
    },
    series: [
      {
        name: 'Nutrition Analysis',
        type: 'radar',
        data: radarData,
        areaStyle: {
          opacity: 0.3,
        },
        lineStyle: {
          width: 2,
        },
        symbolSize: 6,
        emphasis: {
          lineStyle: {
            width: 4,
          },
        },
      },
    ],
    color: ['#00A896', '#02C39A', '#FFE66D', '#2080F0', '#D03050'],
  }
}

watch(() => props.data, updateChart, { immediate: true })
</script>

<style scoped>
.chart {
  height: 400px;
}
</style>
