<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" height="60" :src="avatarUrl" object-cover />
            <div ml-10>
              <p text-20 font-semibold>
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-14 op-60>欢迎使用食智眸：食物识别与营养推荐系统</p>
              <div mt-10 flex flex-wrap gap-10>
                <n-button type="primary" @click="go('/food/recognition')">
                  <template #icon>
                    <n-icon><RestaurantOutline /></n-icon>
                  </template>
                  开始识别
                </n-button>
                <n-button secondary @click="go('/food/history')">
                  <template #icon>
                    <n-icon><TimeOutline /></n-icon>
                  </template>
                  历史记录
                </n-button>
                <n-button tertiary @click="go('/profile')">
                  <template #icon>
                    <n-icon><PersonCircleOutline /></n-icon>
                  </template>
                  完善个人资料
                </n-button>
              </div>
            </div>
          </div>
          <n-space :size="12" :wrap="false">
            <n-statistic v-for="item in statisticData" :key="item.id" v-bind="item"></n-statistic>
          </n-space>
        </div>
      </n-card>

      <n-card
        title="核心功能"
        size="small"
        :segmented="true"
        mt-15
        rounded-10
      >
        <template #header-extra>
          <n-button text type="primary" @click="go('/food/recognition')">立即开始</n-button>
        </template>
        <n-grid cols="1 s:2 m:3 l:4" :x-gap="12" :y-gap="12" mt-10>
          <n-grid-item>
            <n-card hoverable class="cursor-pointer" size="small" @click="go('/food/recognition')">
              <template #header>
                <div flex items-center gap-8>
                  <n-icon size="20" color="#10b981"><RestaurantOutline /></n-icon>
                  <span font-semibold>食物识别分析</span>
                </div>
              </template>
              <p op-70>上传图片，获取识别结果、营养分析与饮食建议。</p>
              <div mt-10 flex justify-end>
                <n-button text type="primary">进入</n-button>
              </div>
            </n-card>
          </n-grid-item>

          <n-grid-item>
            <n-card hoverable class="cursor-pointer" size="small" @click="go('/food/history')">
              <template #header>
                <div flex items-center gap-8>
                  <n-icon size="20" color="#64748b"><TimeOutline /></n-icon>
                  <span font-semibold>识别历史</span>
                </div>
              </template>
              <p op-70>按时间查看识别记录，支持查看详情与批量删除。</p>
              <div mt-10 flex justify-end>
                <n-button text type="primary">进入</n-button>
              </div>
            </n-card>
          </n-grid-item>

          <n-grid-item>
            <n-card hoverable class="cursor-pointer" size="small" @click="go('/profile')">
              <template #header>
                <div flex items-center gap-8>
                  <n-icon size="20" color="#0ea5e9"><PersonCircleOutline /></n-icon>
                  <span font-semibold>个人资料</span>
                </div>
              </template>
              <p op-70>完善身高、体重、性别、年龄，提高个性化建议准确性。</p>
              <div mt-10 flex justify-end>
                <n-button text type="primary">进入</n-button>
              </div>
            </n-card>
          </n-grid-item>

          <n-grid-item>
            <n-card hoverable class="cursor-pointer" size="small" @click="go('/food/management')">
              <template #header>
                <div flex items-center gap-8>
                  <n-icon size="20" color="#f59e0b"><SettingsOutline /></n-icon>
                  <span font-semibold>食物库管理</span>
                </div>
              </template>
              <p op-70>维护食物类别、示例图片与营养信息，支撑识别与分析。</p>
              <div mt-10 flex justify-end>
                <n-button text type="primary">进入</n-button>
              </div>
            </n-card>
          </n-grid-item>
        </n-grid>
      </n-card>

      <n-card title="最近识别记录" size="small" :segmented="true" mt-15 rounded-10>
        <template #header-extra>
          <n-button text type="primary" @click="go('/food/history')">查看全部</n-button>
        </template>

        <div v-if="recentLoading" flex items-center justify-center py-20>
          <n-spin size="small" />
        </div>
        <n-empty v-else-if="recentRecords.length === 0" description="暂无识别记录，去上传一张图片试试吧" />
        <n-list v-else :bordered="false">
          <n-list-item v-for="item in recentRecords" :key="item.id" class="cursor-pointer" @click="go('/food/history')">
            <template #prefix>
              <img
                :src="getImageUrl(item)"
                style="width: 44px; height: 44px; object-fit: cover; border-radius: 8px"
              />
            </template>
            <n-thing :title="`记录 #${item.id}`" :description="item.created_at">
              <template #header-extra>
                <n-space align="center" :size="10">
                  <n-tag size="small" :type="item.status === 'success' ? 'success' : 'error'" :bordered="false">
                    {{ item.status === 'success' ? '成功' : '失败' }}
                  </n-tag>
                  <span op-70>{{ (Number(item.total_energy) || 0).toFixed(1) }} kcal</span>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { RestaurantOutline, TimeOutline, PersonCircleOutline, SettingsOutline } from '@vicons/ionicons5'
import api from '@/api'

const { t } = useI18n({ useScope: 'global' })

const userStore = useUserStore()
const router = useRouter()
const message = useMessage()

const avatarUrl = computed(() => {
  if (!userStore.userInfo.avatar) return 'https://avatars.githubusercontent.com/u/54677442?v=4'
  if (userStore.userInfo.avatar.startsWith('http')) return userStore.userInfo.avatar
  const backendHost = import.meta.env.VITE_APP_API_BASE_URL || ''
  return `${backendHost}${userStore.userInfo.avatar}`
})

const foodCategoryCount = ref('-')
const recognitionRecordCount = ref('-')
const recentLoading = ref(false)
const recentRecords = ref([])

const go = (path) => router.push(path)

const getImageUrl = (row) => {
  if (!row) return ''
  const imagePath = row.annotated_image_path || row.image_path
  if (!imagePath) return ''
  if (/^https?:\/\//.test(imagePath)) return imagePath
  const backendHost = import.meta.env.VITE_APP_API_BASE_URL || ''
  return `${backendHost}${imagePath}`
}

const statisticData = computed(() => [
  {
    id: 0,
    label: '食物库条目',
    value: String(foodCategoryCount.value),
  },
  {
    id: 1,
    label: '识别记录',
    value: String(recognitionRecordCount.value),
  },
  {
    id: 2,
    label: t('views.workbench.label_information'),
    value: '营养建议',
  },
])

const loadStats = async () => {
  try {
    const [categoryRes, historyRes] = await Promise.all([
      api.getFoodCategories({ page: 1, page_size: 1 }),
      api.getFoodHistory({ page: 1, page_size: 1 }),
    ])

    if (categoryRes?.code === 200) foodCategoryCount.value = categoryRes.total ?? 0
    if (historyRes?.code === 200) recognitionRecordCount.value = historyRes.total ?? 0
  } catch (error) {
    foodCategoryCount.value = '-'
    recognitionRecordCount.value = '-'
    message.error('加载统计信息失败')
  }
}

const loadRecent = async () => {
  recentLoading.value = true
  try {
    const res = await api.getFoodHistory({ page: 1, page_size: 5 })
    if (res?.code === 200) {
      recentRecords.value = Array.isArray(res.data) ? res.data : []
    } else {
      recentRecords.value = []
    }
  } catch (error) {
    recentRecords.value = []
  } finally {
    recentLoading.value = false
  }
}

onMounted(async () => {
  await userStore.getUserInfo?.().catch(() => null)
  await Promise.all([loadStats(), loadRecent()])
})
</script>
