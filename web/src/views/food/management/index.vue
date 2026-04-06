<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NImage,
  NInput,
  NInputNumber,
  NSpace,
  NTag,
  NPopconfirm,
  NSelect,
  NUpload,
  NCard,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '食物管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const getImageUrl = (url) => {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  const backendHost = import.meta.env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:9999'
  return `${backendHost}${url}`
}

const foodTypeOptions = ref([
  { label: '蔬菜', value: 'Vegetable' },
  { label: '肉类', value: 'Meat' },
  { label: '水果', value: 'Fruit' },
  { label: '谷物', value: 'Grain' },
  { label: '乳制品', value: 'Dairy' },
  { label: '鱼类', value: 'Fish' },
  { label: '鸡蛋', value: 'Protein' },
])

// 图片上传相关
const uploadFileList = ref([])
const imageUrl = ref('')

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '食物类别',
  initForm: {
    name: '',
    chinese_name: '',
    food_type: '',
    description: '',
    image_url: '',
    nutrition: {
      energy: undefined,
      protein: undefined,
      fat: undefined,
      carbohydrate: undefined,
      fiber: 0,
      sodium: 0,
    },
  },
  doCreate: async () => ({ code: 0 }),
  doUpdate: async () => ({ code: 0 }),
  doDelete: (form) => api.deleteFoodCategory(form.id),
  refresh: () => $table.value?.handleSearch(),
})

// 自定义 handleSave 来处理图片上传和营养信息
const handleSave = async () => {
  try {
    // 验证必填字段
    if (!modalForm.value.name || modalForm.value.name.trim() === '') {
      window.$message?.error('请输入食物名称')
      return
    }

    modalLoading.value = true
    
    const formData = new FormData()
    formData.append('name', modalForm.value.name)
    if (modalForm.value.chinese_name) formData.append('chinese_name', modalForm.value.chinese_name)
    if (modalForm.value.food_type) formData.append('food_type', modalForm.value.food_type)
    if (modalForm.value.description) formData.append('description', modalForm.value.description)

    // 处理图片
    if (uploadFileList.value.length > 0) {
      const file = uploadFileList.value[0].file
      formData.append('image', file)
    } else if (modalForm.value.image_url && modalForm.value.image_url.startsWith('http')) {
      formData.append('image_url', modalForm.value.image_url)
    }

    // 处理营养信息
    const nutritionValues = Object.values(modalForm.value.nutrition || {})
    if (nutritionValues.some(v => v !== undefined && v !== null && v !== '')) {
      formData.append('nutrition', JSON.stringify(modalForm.value.nutrition))
    }

    console.log('准备提交FormData，操作类型：', modalAction.value)
    console.log('食物名称：', modalForm.value.name)

    let result
    try {
      if (modalAction.value === 'add') {
        console.log('调用创建API...')
        result = await api.createFoodCategoryWithUpload(formData)
      } else {
        console.log('调用更新API，ID：', modalForm.value.id)
        result = await api.updateFoodCategoryWithUpload(modalForm.value.id, formData)
      }
      
      console.log('API响应：', result)
      
      if (result && result.code < 400) {
        window.$message?.success(result.msg || (modalAction.value === 'add' ? '食物创建成功！' : '食物更新成功！'))
        uploadFileList.value = []
        imageUrl.value = ''
        modalVisible.value = false
        // 延迟后刷新列表，确保数据已保存
        setTimeout(() => {
          if ($table.value?.handleSearch) {
            $table.value.handleSearch()
          }
        }, 500)
      } else {
        const errorMsg = result?.msg || (modalAction.value === 'add' ? '创建失败，请重试' : '更新失败，请重试')
        window.$message?.error(errorMsg)
        console.error('操作失败，响应：', result)
      }
    } catch (apiError) {
      console.error('API调用异常：', apiError)
      
      let errorMsg = '操作失败，请检查网络连接'
      if (apiError?.response?.data?.msg) {
        errorMsg = apiError.response.data.msg
      } else if (apiError?.response?.status === 422) {
        errorMsg = '表单数据格式错误，请检查输入'
      } else if (apiError?.message) {
        errorMsg = apiError.message
      }
      
      window.$message?.error(errorMsg)
    }
  } catch (error) {
    console.error('未捕获的错误：', error)
    window.$message?.error('发生未知错误，请联系管理员')
  } finally {
    modalLoading.value = false
  }
}

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: '名称',
    key: 'name',
    width: 100,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '中文名',
    key: 'chinese_name',
    width: 100,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'YOLO ID',
    key: 'code',
    width: 50,
    align: 'center',
  },
  {
    title: '类型',
    key: 'food_type',
    width: 60,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: 'info', style: { margin: '2px 3px' } },
        { default: () => row.food_type || '-' }
      )
    },
  },
  {
    title: '热量',
    key: 'nutrition.energy',
    width: 50,
    align: 'center',
    render(row) {
      return row.nutrition?.energy || '-'
    },
  },
  {
    title: '蛋白质',
    key: 'nutrition.protein',
    width: 50,
    align: 'center',
    render(row) {
      return row.nutrition?.protein || '-'
    },
  },
  {
    title: '图片',
    key: 'image',
    width: 80,
    align: 'center',
    render(row) {
      const src = getImageUrl(row.image_url)
      return src
        ? h(NImage, {
            src,
            style: { width: '50px', height: '50px', 'object-fit': 'cover' },
            lazy: true,
          })
        : h(NTag, { type: 'default' }, { default: () => '无' })
    },
  },
  {
    title: '描述',
    key: 'description',
    width: 100,
    ellipsis: { tooltip: true },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => {
                handleEdit(row)
                uploadFileList.value = []
                imageUrl.value = row.image_url || ''
              },
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'put/api/v1/food/categories']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  }
                ),
                [[vPermission, 'delete/api/v1/food/categories']]
              ),
            default: () => '确认删除此食物及其营养信息吗？',
          }
        ),
      ]
    },
  },
]

const handleQueryChange = () => {
  $table.value?.handleSearch()
}

const handleOpenModal = (action) => {
  uploadFileList.value = []
  imageUrl.value = ''
  if (action === 'add') {
    modalForm.value = {
      name: '',
      food_type: '',
      description: '',
      image_url: '',
      nutrition: {
        energy: undefined,
        protein: undefined,
        fat: undefined,
        carbohydrate: undefined,
        fiber: 0,
        sodium: 0,
      },
    }
  }
  handleAdd()
}
</script>

<template>
  <CommonPage show-footer title="食物管理">
    <template #action>
      <NSpace>
        <NButton type="primary" @click="handleOpenModal('add')">
          <template #icon>
            <TheIcon icon="material-symbols:add" />
          </template>
          新增食物
        </NButton>
      </NSpace>
    </template>

    <CrudTable
      ref="$table"
      :columns="columns"
      :get-data="api.getFoodCategories"
      :scroll-x="1200"
    />

    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        :model="modalForm"
        label-placement="top"
      >
        <!-- 食物基本信息 -->
        <NCard title="基本信息" style="margin-bottom: 16px">
          <NFormItem label="食物名称">
            <NInput
              v-model:value="modalForm.name"
              placeholder="请输入食物名称"
              :disabled="modalAction === 'edit'"
            />
          </NFormItem>

          <NFormItem label="中文名">
            <NInput
              v-model:value="modalForm.chinese_name"
              placeholder="请输入食物中文名"
            />
          </NFormItem>

          <NFormItem v-if="modalAction === 'edit'" label="YOLO 类别 ID">
            <NInput
              :value="`${modalForm.code}`"
              :disabled="true"
              placeholder="自动生成"
            />
            <template #label>
              YOLO 类别 ID
              <span style="color: #999; font-size: 12px; margin-left: 4px">（自动生成，不可修改）</span>
            </template>
          </NFormItem>

          <NFormItem label="食物类型">
            <NSelect
              v-model:value="modalForm.food_type"
              :options="foodTypeOptions"
              placeholder="选择食物类型"
              clearable
            />
          </NFormItem>

          <NFormItem label="描述">
            <NInput
              v-model:value="modalForm.description"
              type="textarea"
              placeholder="输入食物描述"
              :rows="2"
            />
          </NFormItem>
        </NCard>

        <!-- 图片上传 -->
        <NCard title="图片" style="margin-bottom: 16px">
          <div v-if="imageUrl && !uploadFileList.length" style="margin-bottom: 12px">
            <div style="margin-bottom: 8px; font-size: 12px; color: #999">当前图片：</div>
            <NImage
              :src="getImageUrl(imageUrl)"
              style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px"
            />
          </div>
          <NUpload
            v-model:file-list="uploadFileList"
            :max="1"
            accept="image/*"
            :action="null"
            list-type="image-card"
          />
          <div style="margin-top: 8px; font-size: 12px; color: #999">
            仅支持 jpg, png 等常见格式
          </div>
        </NCard>

        <!-- 营养信息 -->
        <NCard title="营养信息（每 100g）" style="margin-bottom: 16px">
          <NFormItem label="热量 (kcal)">
            <NInputNumber
              v-model:value="modalForm.nutrition.energy"
              placeholder="热量"
              :min="0"
              :precision="1"
            />
          </NFormItem>

          <NFormItem label="蛋白质 (g)">
            <NInputNumber
              v-model:value="modalForm.nutrition.protein"
              placeholder="蛋白质"
              :min="0"
              :precision="2"
            />
          </NFormItem>

          <NFormItem label="脂肪 (g)">
            <NInputNumber
              v-model:value="modalForm.nutrition.fat"
              placeholder="脂肪"
              :min="0"
              :precision="2"
            />
          </NFormItem>

          <NFormItem label="碳水化合物 (g)">
            <NInputNumber
              v-model:value="modalForm.nutrition.carbohydrate"
              placeholder="碳水化合物"
              :min="0"
              :precision="2"
            />
          </NFormItem>

          <NFormItem label="膳食纤维 (g)">
            <NInputNumber
              v-model:value="modalForm.nutrition.fiber"
              placeholder="膳食纤维"
              :min="0"
              :precision="1"
            />
          </NFormItem>

          <NFormItem label="钠 (mg)">
            <NInputNumber
              v-model:value="modalForm.nutrition.sodium"
              placeholder="钠"
              :min="0"
              :precision="1"
            />
          </NFormItem>
        </NCard>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
