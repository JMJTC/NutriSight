<template>
  <div class="ai-stream" v-html="rendered"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps({ content: { type: String, default: '' } })
const md = new MarkdownIt({ breaks: true, linkify: true })
const rendered = computed(() => md.render(props.content || '...'))
</script>

<style scoped>
.ai-stream { line-height: 1.8; color: #334155; }
.ai-stream :deep(h1), .ai-stream :deep(h2), .ai-stream :deep(h3) { margin: 12px 0 6px; font-weight: 600; }
.ai-stream :deep(ul), .ai-stream :deep(ol) { padding-left: 20px; }
.ai-stream :deep(li) { margin: 4px 0; }
.ai-stream :deep(strong) { color: #1e293b; }
</style>
