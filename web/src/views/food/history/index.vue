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
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, h, reactive } from 'vue'
import { NButton, NTag, useMessage, NPopconfirm, NSpace } from 'naive-ui'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

const message = useMessage()
const loading = ref(false)
const historyList = ref([])
const showDetail = ref(false)
const currentRecord = ref(null)
const checkedRowKeys = ref([])

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
    }
  } catch (error) {
    message.error('获取详情失败')
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
</style>
