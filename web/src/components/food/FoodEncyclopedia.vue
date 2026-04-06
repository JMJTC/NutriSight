<template>
  <n-drawer v-model:show="show" :width="600" placement="right">
    <n-drawer-content closable>
      <template #header>
        <div class="flex items-center py-4 space-x-4">
          <span class="h-10 w-3 rounded-full bg-emerald-500"></span>
          <h3 class="text-4xl font-black tracking-tighter text-slate-900">
            食物百科 (Encyclopedia)
          </h3>
        </div>
      </template>
      <n-input
        v-model:value="searchQuery"
        placeholder="输入食物名称搜索..."
        class="mb-10"
        size="large"
        :style="{ height: '80px', fontSize: '24px', borderRadius: '24px' }"
      >
        <template #prefix>
          <n-icon size="32" class="mr-4 text-slate-400"><SearchOutline /></n-icon>
        </template>
      </n-input>

      <n-list bordered hoverable class="overflow-hidden rounded-[40px] shadow-sm">
        <n-list-item
          v-for="item in filteredFoods"
          :key="item.id"
          class="transition-colors hover:bg-emerald-50/30 !px-8 !py-10"
        >
          <n-thing>
            <template #header>
              <span class="text-3xl font-black tracking-tight text-slate-900">{{ item.name }}</span>
            </template>
            <template #description>
              <n-tag
                size="large"
                type="primary"
                round
                class="mt-3 h-10 px-6 py-1 text-xl font-black"
                >{{ item.category }}</n-tag
              >
            </template>
            <div class="mt-6 text-xl font-bold leading-relaxed text-slate-600">
              {{ item.description }}
            </div>
            <template #footer>
              <n-space size="large" class="mt-8">
                <n-badge
                  :value="item.calories + ' kcal'"
                  type="info"
                  class="mr-10 origin-left scale-150"
                />
                <n-badge
                  :value="'P: ' + item.protein + 'g'"
                  type="success"
                  class="mr-10 origin-left scale-150"
                />
                <n-badge
                  :value="'C: ' + item.carbs + 'g'"
                  type="warning"
                  class="origin-left scale-150"
                />
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
  {
    id: 1,
    name: '苹果',
    category: '水果',
    calories: 52,
    protein: 0.3,
    carbs: 14,
    description: '含有丰富的维生素和膳食纤维。',
  },
  {
    id: 2,
    name: '鸡胸肉',
    category: '肉类',
    calories: 165,
    protein: 31,
    carbs: 0,
    description: '高蛋白低脂肪，健身首选。',
  },
  {
    id: 3,
    name: '西兰花',
    category: '蔬菜',
    calories: 34,
    protein: 2.8,
    carbs: 7,
    description: '超级蔬菜，富含多种微量元素。',
  },
  {
    id: 4,
    name: '糙米',
    category: '谷物',
    calories: 111,
    protein: 2.6,
    carbs: 23,
    description: '全谷物，GI值较低，饱腹感强。',
  },
  {
    id: 5,
    name: '三文鱼',
    category: '水产',
    calories: 208,
    protein: 20,
    carbs: 0,
    description: '富含 Omega-3 脂肪酸。',
  },
])

const filteredFoods = computed(() => {
  if (!searchQuery.value) return foodData.value
  return foodData.value.filter(
    (food) => food.name.includes(searchQuery.value) || food.category.includes(searchQuery.value)
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
