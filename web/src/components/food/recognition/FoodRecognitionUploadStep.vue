<template>
  <div class="upload-step">
    <n-upload
      directory-dnd
      multiple
      action="#"
      :custom-request="customRequest"
      :max="1"
      accept="image/*"
      @remove="$emit('remove')"
    >
      <n-upload-dragger class="upload-dragger-custom">
        <div class="upload-dragger-inner">
          <n-icon size="56" color="#10b981">
            <CloudUploadOutline />
          </n-icon>
          <h3 class="upload-title mt-4">点击或拖拽上传食物图片</h3>
          <p class="upload-desc mt-2">支持 JPG / PNG / WEBP，识别后自动进入下一步</p>
          <div class="mt-4 flex flex-wrap justify-center gap-2">
            <n-tag type="success" round>高精度识别</n-tag>
            <n-tag type="info" round>营养分析</n-tag>
            <n-tag type="warning" round>饮食建议</n-tag>
          </div>
        </div>
      </n-upload-dragger>
    </n-upload>

    <input
      ref="cameraInputRef"
      type="file"
      accept="image/*"
      capture="environment"
      style="display: none"
      @change="handleCameraChange"
    />

    <div class="mt-4 flex justify-center">
      <n-button :disabled="loading" type="primary" secondary @click="cameraInputRef?.click?.()">
        <template #icon>
          <n-icon><CameraOutline /></n-icon>
        </template>
        拍照上传
      </n-button>
    </div>

    <div v-if="loading" class="loading-wrap">
      <n-spin size="medium" />
      <span class="loading-text">AI 正在分析图片，请稍候...</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { CameraOutline, CloudUploadOutline } from '@vicons/ionicons5'

defineProps({
  customRequest: {
    type: Function,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['camera-select', 'remove'])
const cameraInputRef = ref(null)

const handleCameraChange = (event) => {
  const file = event?.target?.files?.[0]
  if (!file) return
  event.target.value = ''
  emit('camera-select', file)
}
</script>

<style scoped>
.upload-step {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.upload-dragger-custom {
  border: 2px dashed #86efac !important;
  border-radius: 14px !important;
  background: #f8fffc !important;
  transition: all 0.2s ease;
}

.upload-dragger-custom:hover {
  border-color: #10b981 !important;
  box-shadow: 0 6px 18px rgba(16, 185, 129, 0.15);
}

.upload-dragger-inner {
  min-height: 270px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

.upload-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}

.upload-desc {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}

.loading-wrap {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.loading-text {
  color: #047857;
  font-size: 14px;
}
</style>
