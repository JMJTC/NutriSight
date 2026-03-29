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
  handleSave: originalHandleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '食物类别',
  initForm: {
    name: '',
    code: undefined,
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
  doCreate: async (form) => {
    const formData = new FormData()
    formData.append('name', form.name)
    formData.append('code', form.code)
    if (form.food_type) formData.append('food_type', form.food_type)
    if (form.description) formData.append('description', form.description)

    // 处理图片
    if (uploadFileList.value.length > 0) {
      const file = uploadFileList.value[0].file
      formData.append('image', file)
    } else if (form.image_url && form.image_url.startsWith('http')) {
      formData.append('image_url', form.image_url)
    }

    // 处理营养信息
    if (form.nutrition && Object.values(form.nutrition).some(v => v !== undefined && v !== null && v !== '')) {
      formData.append('nutrition', JSON.stringify(form.nutrition))
    }

    return api.createFoodCategoryWithUpload(formData)
  },
  doUpdate: async (form) => {
    const formData = new FormData()
    if (form.name) formData.append('name', form.name)
    if (form.food_type) formData.append('food_type', form.food_type)
    if (form.description) formData.append('description', form.description)

    // 处理图片
    if (uploadFileList.value.length > 0) {
      const file = uploadFileList.value[0].file
      formData.append('image', file)
    } else if (form.image_url && form.image_url.startsWith('http')) {
      formData.append('image_url', form.image_url)
    }

    // 处理营养信息
    if (form.nutrition && Object.values(form.nutrition).some(v => v !== undefined && v !== null && v !== '')) {
      formData.append('nutrition', JSON.stringify(form.nutrition))
    }

    return api.updateFoodCategoryWithUpload(form.id, formData)
  },
  doDelete: (form) => api.deleteFoodCategory(form.id),
  refresh: () => $table.value?.handleSearch(),
})

// 自定义 handleSave 来处理图片上传
const handleSave = async () => {
  try {
    await modalFormRef.value?.validate()
    
    // 验证必填字段
    if (!modalForm.value.name) {
      window.$message?.error('请输入食物名称')
      return
    }
    if (modalForm.value.code === undefined || modalForm.value.code === null || modalForm.value.code === '') {
      window.$message?.error('请输入 YOLO 类别 ID')
      return
    }

    modalLoading.value = true
    
    try {
      if (modalAction.value === 'add') {
        await originalHandleSave()
      } else {
        await originalHandleSave()
      }
      uploadFileList.value = []
      imageUrl.value = ''
    } finally {
      modalLoading.value = false
    }
  } catch (error) {
    console.error('Save error:', error)
  }
}

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  {
    title: '名称',
    key: 'name',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'YOLO ID',
    key: 'code',
    width: 60,
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
    title: '热量 (kcal)',
    key: 'nutrition.energy',
    width: 80,
    align: 'center',
    render(row) {
      return row.nutrition?.energy || '-'
    },
  },
  {
    title: '蛋白质 (g)',
    key: 'nutrition.protein',
    width: 80,
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
      return row.image_url
        ? h(NImage, {
            src: row.image_url,
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
      code: undefined,
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
      :on-positive-click="handleSave"
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

          <NFormItem label="YOLO 类别 ID">
            <NInputNumber
              v-model:value="modalForm.code"
              placeholder="请输入 YOLO 类别 ID（创建后无法修改）"
              :disabled="modalAction === 'edit'"
            />
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
              :src="imageUrl"
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
