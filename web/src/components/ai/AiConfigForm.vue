<template>
  <n-card title="AI 配置" size="small">
    <n-form label-placement="left" label-width="100">
      <n-form-item label="API Key">
        <n-input v-model:value="form.api_key" type="password" show-password-on="mousedown" placeholder="输入 API Key" />
      </n-form-item>
      <n-form-item label="模型名称">
        <n-input v-model:value="form.ai_model" placeholder="deepseek-chat, gpt-4o 等" />
      </n-form-item>
      <n-form-item label="API 地址">
        <n-input v-model:value="form.ai_base_url" placeholder="https://api.deepseek.com" />
      </n-form-item>
      <n-space>
        <n-button type="primary" :loading="saving" @click="save">保存</n-button>
        <n-button :loading="testing" @click="test">测试连接</n-button>
      </n-space>
      <div v-if="result" class="mt-3">
        <n-alert :type="result.ok ? 'success' : 'error'">{{ result.msg }}</n-alert>
      </div>
    </n-form>
  </n-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { NCard, NForm, NFormItem, NInput, NButton, NSpace, NAlert, useMessage } from 'naive-ui'
import api from '@/api'

const msg = useMessage()
const saving = ref(false); const testing = ref(false); const result = ref(null)
const form = ref({ api_key: '', ai_model: 'deepseek-chat', ai_base_url: 'https://api.deepseek.com' })

onMounted(async () => {
  try {
    const r = await api.getAiConfig()
    if (r.code === 200) {
      form.value.ai_model = r.data.ai_model || 'deepseek-chat'
      form.value.ai_base_url = r.data.ai_base_url || 'https://api.deepseek.com'
    }
  } catch {}
})

async function save() {
  saving.value = true
  try {
    const p = { ai_model: form.value.ai_model, ai_base_url: form.value.ai_base_url }
    if (form.value.api_key) p.api_key = form.value.api_key
    if ((await api.updateAiConfig(p)).code === 200) { msg.success('已保存'); form.value.api_key = '' }
  } catch { msg.error('保存失败') }
  finally { saving.value = false }
}

async function test() {
  testing.value = true; result.value = null
  if (form.value.api_key) await save()
  try {
    const r = await api.aiTestConnection()
    result.value = r.code === 200 ? { ok: true, msg: `连接成功 — ${r.data.model}` } : { ok: false, msg: r.msg }
  } catch { result.value = { ok: false, msg: '连接失败' } }
  finally { testing.value = false }
}
</script>
