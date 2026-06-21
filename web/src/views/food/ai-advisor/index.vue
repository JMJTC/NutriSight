<template>
  <div class="advisor-page">
    <n-layout has-sider class="layout">
      <n-layout-content class="chat-area"><AiChatPanel ref="cr" :context="ctx" /></n-layout-content>
      <n-layout-sider width="260" bordered class="sidebar">
        <h4>上下文</h4>
        <n-empty v-if="!ctx" description="未关联记录" size="small" />
        <n-tag v-else type="info">{{ ctx }}</n-tag>
        <n-divider />
        <n-button size="small" ghost block @click="cr?.clearMessages()">清空对话</n-button>
      </n-layout-sider>
    </n-layout>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { NLayout, NLayoutContent, NLayoutSider, NDivider, NButton, NTag, NEmpty } from 'naive-ui'
import AiChatPanel from '@/components/ai/AiChatPanel.vue'
const cr = ref(null); const ctx = ref('')
</script>

<style scoped>
.advisor-page,.layout { height:100% }
.chat-area { height:100%; display:flex; flex-direction:column }
.sidebar { padding:16px }
.sidebar h4 { margin:0 0 12px; font-size:15px; color:#334155 }
</style>
