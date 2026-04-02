<template>
  <v-chart class="chart" :option="option" autoresize />
</template>

<script setup>
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { HeatmapChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { ref, watch } from 'vue'

use([
  CanvasRenderer,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  GridComponent,
])

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
})

const option = ref({})

const updateChart = () => {
  const source = Array.isArray(props.data) ? props.data : []
  if (source.length === 0) {
    option.value = {
      title: {
        text: '暂无置信度数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#94a3b8',
          fontSize: 14,
          fontWeight: 500,
        },
      },
    }
    return
  }

  const foodNames = source.map((item) => item.food_name || '未知食物')
  const confidenceData = source.map((item, index) => [
    index,
    0,
    Number(((Number(item.confidence) || 0) * 100).toFixed(1)),
  ])

  option.value = {
    title: {
      text: '置信度分析 (Confidence Heatmap)',
      left: 'center',
      textStyle: {
        color: '#00A896',
        fontSize: 14,
      },
    },
    tooltip: {
      position: 'top',
      formatter: (params) => {
        return `${foodNames[params.data[0]]}: ${params.data[2]}%`
      },
    },
    grid: {
      height: '50%',
      top: '25%',
    },
    xAxis: {
      type: 'category',
      data: foodNames,
      splitArea: {
        show: true,
      },
      axisLabel: {
        interval: 0,
        rotate: 30,
      },
    },
    yAxis: {
      type: 'category',
      data: ['置信度'],
      splitArea: {
        show: true,
      },
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#FFE66D', '#02C39A', '#00A896'],
      },
    },
    series: [
      {
        name: 'Confidence',
        type: 'heatmap',
        data: confidenceData,
        label: {
          show: true,
          formatter: (params) => {
            return params.data[2] + '%'
          },
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }
}

watch(() => props.data, updateChart, { immediate: true })
</script>

<style scoped>
.chart {
  height: 300px;
}
</style>
