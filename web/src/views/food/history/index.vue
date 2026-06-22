<template>
  <div class="food-history">
    <n-card title="识别历史记录">
      <template #header-extra>
        <n-button type="error" ghost :disabled="!checkedRowKeys.length" @click="handleBatchDelete">
          <template #icon>
            <TheIcon icon="mdi:delete" :size="18" />
          </template>
          批量删除
        </n-button>
      </template>

      <n-data-table
        remote
        :columns="columns"
        :data="historyList"
        :pagination="pagination"
        :loading="loading"
        :row-key="(row) => row.id"
        @update:checked-row-keys="handleCheck"
      />
    </n-card>

    <n-modal v-model:show="showDetail" preset="card" style="width: 800px" title="识别详情">
      <div v-if="currentRecord" class="record-detail">
        <div class="image-area">
          <n-image :src="getImageUrl(currentRecord)" object-fit="contain" />
        </div>
        <n-divider />
        <div class="analysis-result">
          <n-descriptions bordered title="营养分析">
            <n-descriptions-item label="总热量">
              {{ currentRecord.analysis?.total_calories?.toFixed(2) }} kcal
            </n-descriptions-item>
            <n-descriptions-item label="总碳水">
              {{ currentRecord.analysis?.total_carbs?.toFixed(2) }} g
            </n-descriptions-item>
            <n-descriptions-item label="总蛋白质">
              {{ currentRecord.analysis?.total_protein?.toFixed(2) }} g
            </n-descriptions-item>
            <n-descriptions-item label="总脂肪">
              {{ currentRecord.analysis?.total_fat?.toFixed(2) }} g
            </n-descriptions-item>
          </n-descriptions>

          <n-divider dashed>识别物品</n-divider>
          <n-table size="small" :single-line="false">
            <thead>
              <tr>
                <th>食物名称</th>
                <th>置信度</th>
                <th>数量</th>
                <th>热量(kcal)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in currentRecord.details" :key="item.id">
                <td>{{ item.food_name }}</td>
                <td>{{ (item.confidence * 100).toFixed(1) }}%</td>
                <td>{{ item.count }}</td>
                <td>{{ item.calories }}</td>
              </tr>
            </tbody>
          </n-table>

          <n-divider dashed>AI 营养建议</n-divider>
          <div v-if="recommendationLoading && !aiContent" class="recommend-loading">
            <n-spin size="small" />
            <span>AI 正在生成建议...</span>
          </div>
          <AiStreamRenderer v-else-if="aiContent" :content="aiContent" />
          <div v-else class="recommend-actions">
            <n-button type="primary" ghost size="small" @click="generateAiSuggestion">
              <template #icon><TheIcon icon="carbon:ai-status" :size="16" /></template>
              生成 AI 建议
            </n-button>
          </div>
          <div v-if="aiContent && !recommendationLoading" class="recommend-actions mt-2">
            <n-button size="tiny" ghost @click="generateAiSuggestion">重新生成</n-button>
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, h, reactive } from 'vue'
import { NButton, NTag, useMessage, NPopconfirm, NSpace } from 'naive-ui'
import { CheckmarkCircleOutline } from '@vicons/ionicons5'
import api from '@/api'
import { getToken } from '@/utils'
import TheIcon from '@/components/icon/TheIcon.vue'
import AiStreamRenderer from '@/components/ai/AiStreamRenderer.vue'

const message = useMessage()
const loading = ref(false)
const historyList = ref([])
const showDetail = ref(false)
const currentRecord = ref(null)
const checkedRowKeys = ref([])
const recommendationLoading = ref(false)
const recommendationTips = ref([])
const aiContent = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  prefix({ itemCount }) {
    return `共 ${itemCount} 条`
  },
  onChange: (page) => {
    pagination.page = page
    fetchHistory()
  },
  onUpdatePageSize: (pageSize) => {
    pagination.pageSize = pageSize
    pagination.page = 1
    fetchHistory()
  },
})

const columns = [
  {
    type: 'selection',
  },
  {
    title: 'ID',
    key: 'id',
    width: 80,
  },
  {
    title: '图片预览',
    key: 'image_path',
    render(row) {
      return h('img', {
        src: getImageUrl(row),
        style: 'width: 50px; height: 50px; object-fit: cover; border-radius: 4px;',
      })
    },
  },
  {
    title: '识别状态',
    key: 'status',
    render(row) {
      return h(
        NTag,
        {
          type: row.status === 'success' ? 'success' : 'error',
          bordered: false,
        },
        { default: () => (row.status === 'success' ? '成功' : '失败') }
      )
    },
  },
  {
    title: '总热量 (kcal)',
    key: 'total_energy',
    render(row) {
      return row.total_energy?.toFixed(2) || '0.00'
    },
  },
  {
    title: '识别时间',
    key: 'created_at',
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    render(row) {
      return h(NSpace, null, {
        default: () => [
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              ghost: true,
              onClick: () => viewDetail(row),
            },
            { default: () => '详情' }
          ),
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleDelete(row.id),
            },
            {
              trigger: () =>
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                    ghost: true,
                  },
                  { default: () => '删除' }
                ),
              default: () => '确定要删除这条识别记录吗？',
            }
          ),
        ],
      })
    },
  },
]

const handleCheck = (rowKeys) => {
  checkedRowKeys.value = rowKeys
}

const handleDelete = async (id) => {
  try {
    const res = await api.deleteFoodRecord(id)
    if (res.code === 200) {
      message.success('删除成功')
      fetchHistory()
    }
  } catch (error) {
    message.error('删除失败')
  }
}

const handleBatchDelete = async () => {
  if (!checkedRowKeys.value.length) return

  window.$dialog?.warning({
    title: '批量删除',
    content: `确定要删除选中的 ${checkedRowKeys.value.length} 条记录吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await api.batchDeleteFoodRecords(checkedRowKeys.value)
        if (res.code === 200) {
          message.success(res.msg || '批量删除成功')
          checkedRowKeys.value = []
          fetchHistory()
        }
      } catch (error) {
        message.error('批量删除失败')
      }
    },
  })
}

const getImageUrl = (row) => {
  if (!row) return ''
  const imagePath = row.annotated_image_path || row.image_path
  if (!imagePath) return ''
  if (/^https?:\/\//.test(imagePath)) {
    return imagePath
  }
  return imagePath
}

const fetchHistory = async () => {
  loading.value = true
  try {
    const res = await api.getFoodHistory({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    if (res.code === 200) {
      historyList.value = res.data
      pagination.itemCount = res.total
    }
  } catch (error) {
    message.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = async (row) => {
  try {
    const res = await api.getFoodRecordDetail(row.id)
    if (res.code === 200) {
      currentRecord.value = res.data
      showDetail.value = true
      recommendationTips.value = []
      aiContent.value = ''
      recommendationLoading.value = true

      // Check cache first
      try {
        const cached = await api.getAiRecommendation(row.id)
        if (cached.code === 200 && cached.data?.content) {
          aiContent.value = cached.data.content
          recommendationLoading.value = false
          return
        }
      } catch {}

      // No cache — show generate button instead of auto-calling
      recommendationLoading.value = false
    }
  } catch (error) { message.error('获取详情失败') }
}

async function generateAiSuggestion() {
  if (!currentRecord.value) return
  const recordId = currentRecord.value.record_id || currentRecord.value.id
  aiContent.value = ''
  recommendationTips.value = []
  recommendationLoading.value = true

  const token = getToken() || ''
  try {
    const response = await fetch(api.aiAnalyzeRecordStreamUrl(recordId), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'token': token },
    })
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token') { aiContent.value += data.content }
            else if (data.type === 'error') {
              if (data.content && data.content.includes('AI API Key')) {
                recommendationLoading.value = false
                await loadRuleBasedFallback(recordId)
                return
              }
              recommendationTips.value = [data.content || 'AI 服务异常']
            }
          } catch {}
        }
      }
    }
  } catch {
    if (!aiContent.value) recommendationTips.value = ['AI 分析请求失败']
  } finally {
    recommendationLoading.value = false
  }
}

async function loadRuleBasedFallback(recordId) {
  recommendationLoading.value = true
  try {
    const res = await api.generateFoodRecordRecommendation(recordId)
    const tips = Array.isArray(res.data?.tips) ? res.data.tips : []
    recommendationTips.value = tips
    if (tips.length > 0) {
      aiContent.value =
        '> ⚠️ AI 智能分析暂不可用（未配置 API Key），以下为基于规则生成的分析：\n\n' +
        tips.map((tip, i) => `${i + 1}. ${tip}`).join('\n\n')
    } else {
      aiContent.value = ''
    }
  } catch {
    recommendationTips.value = ['基于规则的分析生成失败']
  } finally {
    recommendationLoading.value = false
  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.food-history {
  padding: 24px;
  height: 100%;
  min-height: 0;
  overflow: auto;
}
.record-detail {
  padding: 12px;
  max-height: calc(100vh - 180px);
  overflow: auto;
}
.image-area {
  text-align: center;
  margin-bottom: 24px;
  max-height: 640px;
  overflow: auto;
}
.image-area img,
.image-area .n-image {
  max-width: 100%;
  max-height: 620px;
  width: auto;
  height: auto;
  object-fit: contain;
}
.recommend-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #64748b;
  font-size: 14px;
}
.advice-text {
  color: #334155;
  line-height: 1.7;
}
.recommend-actions {
  display: flex;
  justify-content: center;
  padding: 16px;
}
.mt-2 {
  margin-top: 8px;
}
</style>
