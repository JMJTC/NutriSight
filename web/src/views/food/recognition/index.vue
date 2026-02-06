<template>
  <div class="food-recognition">
    <n-card title="食物识别" class="upload-card">
      <div class="upload-area">
        <n-upload
          multiple
          directory-dnd
          action="#"
          :custom-request="handleUpload"
          :max="1"
          accept="image/*"
        >
          <n-upload-dragger>
            <div style="margin-bottom: 12px">
              <n-icon size="48" :depth="3">
                <CloudUploadOutline />
              </n-icon>
            </div>
            <n-text style="font-size: 16px">
              点击或者拖拽文件到该区域来上传
            </n-text>
            <n-p depth="3" style="margin: 8px 0 0 0">
              支持 JPG、PNG 格式图片，请上传清晰的食物图片
            </n-p>
          </n-upload-dragger>
        </n-upload>
      </div>
      
      <div v-if="loading" class="loading-area">
        <n-spin size="large">
          <template #description>
            正在识别中，请稍候...
          </template>
        </n-spin>
      </div>

      <div v-if="result" class="result-area">
        <n-divider>识别结果</n-divider>
        <div class="result-container">
          <div class="image-wrapper" ref="imageWrapper">
            <img :src="imageUrl" alt="Original Image" @load="drawImage" ref="imageRef" />
            <canvas ref="canvasRef" class="overlay-canvas"></canvas>
          </div>
          
          <div class="nutrition-info">
            <n-card title="营养成分分析" size="small">
              <n-descriptions bordered label-placement="left" :column="1">
                <n-descriptions-item label="总热量">
                  {{ result.nutrition.total_calories.toFixed(2) }} kcal
                </n-descriptions-item>
                <n-descriptions-item label="总碳水化合物">
                  {{ result.nutrition.total_carbs.toFixed(2) }} g
                </n-descriptions-item>
                <n-descriptions-item label="总蛋白质">
                  {{ result.nutrition.total_protein.toFixed(2) }} g
                </n-descriptions-item>
                <n-descriptions-item label="总脂肪">
                  {{ result.nutrition.total_fat.toFixed(2) }} g
                </n-descriptions-item>
              </n-descriptions>
              
              <n-divider dashed>识别详情</n-divider>
              <n-list hoverable>
                <n-list-item v-for="(item, index) in result.details" :key="index">
                  <n-thing :title="item.food_name">
                    <template #description>
                      <n-space size="small">
                        <n-tag type="success" size="small">置信度: {{ (item.confidence * 100).toFixed(1) }}%</n-tag>
                        <n-tag type="warning" size="small">数量: {{ item.count }}</n-tag>
                      </n-space>
                    </template>
                    <n-grid :cols="4" :x-gap="12">
                      <n-grid-item>
                        <div class="nutrition-item">
                          <span class="label">热量</span>
                          <span class="value">{{ item.nutrition.calories }}</span>
                        </div>
                      </n-grid-item>
                      <n-grid-item>
                        <div class="nutrition-item">
                          <span class="label">碳水</span>
                          <span class="value">{{ item.nutrition.carbs }}</span>
                        </div>
                      </n-grid-item>
                      <n-grid-item>
                        <div class="nutrition-item">
                          <span class="label">蛋白质</span>
                          <span class="value">{{ item.nutrition.protein }}</span>
                        </div>
                      </n-grid-item>
                      <n-grid-item>
                        <div class="nutrition-item">
                          <span class="label">脂肪</span>
                          <span class="value">{{ item.nutrition.fat }}</span>
                        </div>
                      </n-grid-item>
                    </n-grid>
                  </n-thing>
                </n-list-item>
              </n-list>
            </n-card>
          </div>
        </div>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { CloudUploadOutline } from '@vicons/ionicons5'
import { useMessage } from 'naive-ui'
import api from '@/api'

const message = useMessage()
const loading = ref(false)
const result = ref(null)
const imageUrl = ref('')
const imageRef = ref(null)
const canvasRef = ref(null)

const handleUpload = async ({ file, onFinish, onError }) => {
  loading.value = true
  result.value = null
  
  const formData = new FormData()
  formData.append('file', file.file)
  
  // Create object URL for preview
  imageUrl.value = URL.createObjectURL(file.file)

  try {
    const res = await api.recognizeFood(formData)
    if (res.code === 200) {
      result.value = res.data
      message.success('识别成功')
      onFinish()
      await nextTick()
      drawImage()
    } else {
      message.error(res.msg || '识别失败')
      onError()
    }
  } catch (error) {
    message.error('请求出错')
    onError()
  } finally {
    loading.value = false
  }
}

const drawImage = () => {
  if (!result.value || !imageRef.value || !canvasRef.value) return

  const img = imageRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  
  // Match canvas size to image display size
  canvas.width = img.width
  canvas.height = img.height
  
  // Calculate scaling factor if image is resized by CSS
  const scaleX = img.width / img.naturalWidth
  const scaleY = img.height / img.naturalHeight

  // Draw bounding boxes
  ctx.lineWidth = 3
  ctx.strokeStyle = '#18a058'
  ctx.font = '16px Arial'
  ctx.fillStyle = '#18a058'

  result.value.details.forEach(item => {
    if (item.box) {
      const [x1, y1, x2, y2] = item.box
      const rectX = x1 * scaleX
      const rectY = y1 * scaleY
      const rectW = (x2 - x1) * scaleX
      const rectH = (y2 - y1) * scaleY

      // Draw box
      ctx.strokeRect(rectX, rectY, rectW, rectH)
      
      // Draw label background
      const label = `${item.food_name} ${(item.confidence * 100).toFixed(0)}%`
      const textWidth = ctx.measureText(label).width
      ctx.fillRect(rectX, rectY - 25, textWidth + 10, 25)
      
      // Draw text
      ctx.fillStyle = '#ffffff'
      ctx.fillText(label, rectX + 5, rectY - 7)
      ctx.fillStyle = '#18a058' // Reset fill style for next box
    }
  })
}
</script>

<style scoped>
.food-recognition {
  padding: 24px;
}
.upload-card {
  max-width: 1200px;
  margin: 0 auto;
}
.loading-area {
  padding: 40px;
  display: flex;
  justify-content: center;
}
.result-area {
  margin-top: 24px;
}
.result-container {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.image-wrapper {
  position: relative;
  flex: 1;
  min-width: 300px;
  max-width: 800px;
}
.image-wrapper img {
  width: 100%;
  display: block;
  border-radius: 4px;
}
.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}
.nutrition-info {
  flex: 1;
  min-width: 300px;
}
.nutrition-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.nutrition-item .label {
  font-size: 12px;
  color: #666;
}
.nutrition-item .value {
  font-weight: bold;
}
</style>