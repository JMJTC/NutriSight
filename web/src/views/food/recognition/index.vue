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
        <div class="debug-info">
          <p>原始图片路径: {{ result.image_path }}</p>
          <p>标注图片路径: {{ result.annotated_image_path }}</p>
          <p>最终图片URL: {{ getImageUrl(result.annotated_image_path || result.image_path) }}</p>
        </div>
        <div class="result-container">
          <div class="image-wrapper" ref="imageWrapper">
            <img 
              :src="getImageUrl(result.annotated_image_path || result.image_path)" 
              alt="识别结果" 
              @load="onImageLoad" 
              @error="onImageError"
              ref="imageRef" 
            />
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
      console.log('Recognition result:', result.value)
      message.success('识别成功')
      onFinish()
    } else {
      message.error(res.msg || '识别失败')
      onError()
    }
  } catch (error) {
    console.error('Upload error:', error)
    message.error('请求出错')
    onError()
  } finally {
    loading.value = false
  }
}

const getImageUrl = (path) => {
  if (!path) return ''
  // Assuming the backend serves static files at the root
  // Use the proxy target for images
  return `http://127.0.0.1:9999${path}`
}

const onImageLoad = () => {
  console.log('Image loaded successfully')
}

const onImageError = (event) => {
  console.error('Image load failed:', event)
  message.error('图片加载失败')
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
.debug-info {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 12px;
  color: #666;
}
.debug-info p {
  margin: 4px 0;
  word-break: break-all;
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
  max-width: 100%;
  max-height: 80vh; /* 限制最大高度为视窗高度的80% */
  overflow: auto; /* 添加滚动条 */
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.image-wrapper img {
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 4px;
  object-fit: contain; /* 保持图片比例 */
  flex-shrink: 0; /* 防止图片被压缩 */
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