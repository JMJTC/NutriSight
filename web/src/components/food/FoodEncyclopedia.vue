<template>
  <n-drawer v-model:show="show" :width="600" placement="right">
    <n-drawer-content closable>
      <template #header>
        <div class="flex items-center space-x-4 py-4">
          <span class="w-3 h-10 bg-emerald-500 rounded-full"></span>
          <h3 class="text-4xl font-black text-slate-900 tracking-tighter">食物百科 (Encyclopedia)</h3>
        </div>
      </template>
      <n-input v-model:value="searchQuery" placeholder="输入食物名称搜索..." class="mb-10" size="large" 
        :style="{ height: '80px', fontSize: '24px', borderRadius: '24px' }">
        <template #prefix>
          <n-icon size="32" class="mr-4 text-slate-400"><SearchOutline /></n-icon>
        </template>
      </n-input>

      <n-list hoverable bordered class="rounded-[40px] overflow-hidden shadow-sm">
        <n-list-item v-for="item in filteredFoods" :key="item.id" class="!py-10 !px-8 hover:bg-emerald-50/30 transition-colors">
          <n-thing>
            <template #header>
              <span class="text-3xl font-black text-slate-900 tracking-tight">{{ item.name }}</span>
            </template>
            <template #description>
              <n-tag size="large" type="primary" round class="font-black mt-3 px-6 py-1 h-10 text-xl">{{ item.category }}</n-tag>
            </template>
            <div class="mt-6 text-xl text-slate-600 font-bold leading-relaxed">
              {{ item.description }}
            </div>
            <template #footer>
              <n-space size="large" class="mt-8">
                <n-badge :value="item.calories + ' kcal'" type="info" class="scale-150 origin-left mr-10" />
                <n-badge :value="'P: ' + item.protein + 'g'" type="success" class="scale-150 origin-left mr-10" />
                <n-badge :value="'C: ' + item.carbs + 'g'" type="warning" class="scale-150 origin-left" />
              </n-space>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { SearchOutline } from '@vicons/ionicons5'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:visible'])

const show = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const searchQuery = ref('')

const foodData = ref([
  { id: 1, name: '苹果', category: '水果', calories: 52, protein: 0.3, carbs: 14, description: '含有丰富的维生素和膳食纤维。' },
  { id: 2, name: '鸡胸肉', category: '肉类', calories: 165, protein: 31, carbs: 0, description: '高蛋白低脂肪，健身首选。' },
  { id: 3, name: '西兰花', category: '蔬菜', calories: 34, protein: 2.8, carbs: 7, description: '超级蔬菜，富含多种微量元素。' },
  { id: 4, name: '糙米', category: '谷物', calories: 111, protein: 2.6, carbs: 23, description: '全谷物，GI值较低，饱腹感强。' },
  { id: 5, name: '三文鱼', category: '水产', calories: 208, protein: 20, carbs: 0, description: '富含 Omega-3 脂肪酸。' },
])

const filteredFoods = computed(() => {
  if (!searchQuery.value) return foodData.value
  return foodData.value.filter(food => 
    food.name.includes(searchQuery.value) || 
    food.category.includes(searchQuery.value)
  )
})
</script>

<style scoped>
.mb-4 {
  margin-bottom: 1rem;
}
.mt-2 {
  margin-top: 0.5rem;
}
</style>
