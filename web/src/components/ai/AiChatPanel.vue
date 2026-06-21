<template>
  <div class="chat-panel">
    <div class="chat-msgs" ref="mc">
      <n-empty v-if="!msgs.length && !streaming" description="向 AI 营养顾问提问吧" class="chat-empty" />
      <div v-for="(m,i) in msgs" :key="i" class="chat-msg" :class="m.role">
        <n-avatar v-if="m.role==='assistant'" :size="32" src="/logo.png" />
        <n-avatar v-else :size="32">U</n-avatar>
        <div class="msg-body">
          <div class="msg-role">{{ m.role==='assistant'?'AI 顾问':'我' }}</div>
          <AiStreamRenderer v-if="m.role==='assistant'" :content="m.content" />
          <div v-else class="msg-text">{{ m.content }}</div>
        </div>
      </div>
      <div v-if="streaming" class="chat-msg assistant">
        <n-avatar :size="32" src="/logo.png" />
        <div class="msg-body"><div class="msg-role">AI 顾问</div><AiStreamRenderer :content="sc" /></div>
      </div>
    </div>
    <div class="chat-input">
      <n-input v-model:value="input" type="textarea" :autosize="{minRows:1,maxRows:4}"
        placeholder="输入营养问题..." :disabled="streaming" @keydown.enter.exact.prevent="send" />
      <n-button type="primary" :disabled="!input.trim()||streaming" :loading="streaming" @click="send">
        <TheIcon icon="mdi:send" :size="18" />
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { NEmpty, NAvatar, NInput, NButton, useMessage } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import AiStreamRenderer from './AiStreamRenderer.vue'
import api from '@/api'

const props = defineProps({ context: { type: String, default: '' } })
const msgRef = useMessage()
const msgs = ref([])
const input = ref('')
const streaming = ref(false)
const sc = ref('')
const mc = ref(null)

async function send() {
  const t = input.value.trim()
  if (!t || streaming.value) return
  msgs.value.push({ role: 'user', content: t }); input.value = ''
  streaming.value = true; sc.value = ''; await nextTick(); scroll()

  try {
    const tok = localStorage.getItem('access_token') || ''
    const r = await fetch(api.aiChatStreamUrl(), {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'token': tok },
      body: JSON.stringify({ messages: msgs.value.map(m=>({role:m.role,content:m.content})), context: props.context })
    })
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n'); buf = lines.pop() || ''
      for (const ln of lines) {
        if (ln.startsWith('data: ')) {
          try {
            const d = JSON.parse(ln.slice(6))
            if (d.type === 'token') sc.value += d.content
            else if (d.type === 'done') { msgs.value.push({ role: 'assistant', content: d.content || sc.value }); sc.value = '' }
            else if (d.type === 'error') msgRef.error(d.content)
          } catch {}
        }
      }
    }
  } catch { msgRef.error('连接失败') }
  finally { streaming.value = false; sc.value = ''; await nextTick(); scroll() }
}

function scroll() { if (mc.value) mc.value.scrollTop = mc.value.scrollHeight }
function clearMessages() { msgs.value = [] }
defineExpose({ clearMessages })
</script>

<style scoped>
.chat-panel { display:flex; flex-direction:column; height:100% }
.chat-msgs { flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:16px }
.chat-empty { margin:auto }
.chat-msg { display:flex; gap:12px; max-width:85% }
.chat-msg.user { align-self:flex-end; flex-direction:row-reverse }
.chat-msg.assistant { align-self:flex-start }
.msg-body { background:#f8fafc; border-radius:12px; padding:12px 16px; min-width:0 }
.chat-msg.user .msg-body { background:#dbeafe }
.msg-role { font-size:12px; color:#64748b; margin-bottom:4px; font-weight:600 }
.msg-text { color:#334155; line-height:1.7; white-space:pre-wrap }
.chat-input { display:flex; gap:8px; padding:12px 16px; border-top:1px solid #e2e8f0; background:#fff }
</style>
