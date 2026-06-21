import { computed, onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useUserStore } from '@/store'

export function useFoodRecognition() {
  const message = useMessage()
  const router = useRouter()
  const userStore = useUserStore()

  const loading = ref(false)
  const result = ref(null)
  const currentStep = ref(1)
  const stepStatus = ref('process')
  const showEncyclopedia = ref(false)
  const hasShownProfileDialog = ref(false)
  const recommendationTips = ref([])
  const recommendationLoading = ref(false)
  const aiAnalysis = ref('')
  const aiAnalysisLoading = ref(false)

  const isValidHeight = (value) => Number.isFinite(value) && value >= 130 && value <= 250
  const isValidWeight = (value) => Number.isFinite(value) && value >= 30 && value <= 200
  const isValidGender = (value) => Number.isFinite(value) && value >= 1 && value <= 3
  const isValidAge = (value) => Number.isFinite(value) && value >= 1 && value <= 120

  const missingProfileFields = computed(() => {
    const heightCm = Number(userStore.userInfo?.height_cm)
    const weightKg = Number(userStore.userInfo?.weight_kg)
    const gender = Number(userStore.userInfo?.gender)
    const age = Number(userStore.userInfo?.age)

    const missing = []
    if (!isValidHeight(heightCm)) missing.push('身高')
    if (!isValidWeight(weightKg)) missing.push('体重')
    if (!isValidGender(gender)) missing.push('性别')
    if (!isValidAge(age)) missing.push('年龄')
    return missing
  })

  const isProfileComplete = computed(() => missingProfileFields.value.length === 0)

  const promptCompleteProfile = (actionLabel = '使用核心功能') => {
    if (hasShownProfileDialog.value) return
    hasShownProfileDialog.value = true
    const missingText = missingProfileFields.value.join('、')
    const content = missingText
      ? `为保证识别分析与个性化建议准确性，${actionLabel}前请先完善：${missingText}。现在去完善吗？`
      : `为保证识别分析与个性化建议准确性，${actionLabel}前请先完善个人信息。现在去完善吗？`
    if (typeof $dialog?.confirm === 'function') {
      $dialog.confirm({
        title: '请先完善个人信息',
        type: 'warning',
        content,
        async confirm() {
          await router.push('/profile')
        },
        cancel() {
          message.warning('请先完善个人信息后再使用该功能')
        },
      })
    } else {
      message.warning(content)
    }
  }

  const ensureProfileComplete = (actionLabel) => {
    if (isProfileComplete.value) return true
    promptCompleteProfile(actionLabel)
    return false
  }

  const mappedDetails = computed(() => {
    const details = Array.isArray(result.value?.details) ? result.value.details : []
    return details.map((item, index) => {
      const nutrition = item?.nutrition || {}
      const classId = Number(item?.class_id)
      const foodNameZh = item?.food_name_zh || item?.food_name || `食物${index + 1}`
      const foodNameEn = item?.food_name_en || item?.food_name || foodNameZh
      return {
        class_id: Number.isFinite(classId) ? classId : -1,
        food_name: foodNameZh,
        food_name_zh: foodNameZh,
        food_name_en: foodNameEn,
        confidence: Number(item?.confidence) || 0,
        nutrition: {
          calories: Number(nutrition.calories) || 0,
          protein: Number(nutrition.protein) || 0,
          carbs: Number(nutrition.carbs) || 0,
          fat: Number(nutrition.fat) || 0,
          fiber: Number(nutrition.fiber) || 0,
          sodium: Number(nutrition.sodium) || 0,
        },
      }
    })
  })

  const primaryDetail = computed(() => {
    const list = mappedDetails.value
    if (!list.length) return null
    return list.reduce(
      (best, current) => (current.confidence > best.confidence ? current : best),
      list[0]
    )
  })

  const safeDetails = computed(() => {
    const best = primaryDetail.value
    return best ? [best] : []
  })

  const currentNutrition = computed(() => {
    const best = primaryDetail.value
    if (!best) return { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0, sodium: 0 }
    return {
      calories: Number(best.nutrition?.calories) || 0,
      protein: Number(best.nutrition?.protein) || 0,
      carbs: Number(best.nutrition?.carbs) || 0,
      fat: Number(best.nutrition?.fat) || 0,
      fiber: Number(best.nutrition?.fiber) || 0,
      sodium: Number(best.nutrition?.sodium) || 0,
    }
  })

  const primaryFood = computed(() => {
    const best = primaryDetail.value
    if (!best) return { food_name_zh: '', food_name_en: '', confidence: null }
    return {
      food_name_zh: best.food_name_zh || '',
      food_name_en: best.food_name_en || '',
      confidence: Number.isFinite(best.confidence) ? best.confidence : null,
    }
  })

  const resetWizard = () => {
    result.value = null
    currentStep.value = 1
    recommendationTips.value = []
  }

  const onRemove = () => {
    resetWizard()
  }

  const loadRecommendation = async () => {
    if (!ensureProfileComplete('生成饮食建议')) return
    if (!result.value?.record_id || recommendationLoading.value) return

    recommendationLoading.value = true
    try {
      const res = await api.generateFoodRecordRecommendation(result.value.record_id)
      recommendationTips.value = Array.isArray(res.data?.tips) ? res.data.tips : []
    } catch (error) {
      recommendationTips.value = []
      message.error(error?.message || '生成建议请求出错')
    } finally {
      recommendationLoading.value = false
    }
  }

  const fetchAiAnalysis = async (recordId) => {
    if (!recordId) return
    aiAnalysisLoading.value = true
    aiAnalysis.value = ''
    const token = localStorage.getItem('access_token') || ''
    try {
      const response = await fetch(api.aiAnalyzeRecordStreamUrl(recordId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'token': token },
      })
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'token') aiAnalysis.value += data.content
            } catch {}
          }
        }
      }
    } catch {} finally { aiAnalysisLoading.value = false }
  }

  const uploadByRawFile = async (rawFile) => {
    if (!ensureProfileComplete('上传识别')) return

    loading.value = true
    result.value = null
    recommendationTips.value = []

    const formData = new FormData()
    formData.append('file', rawFile)

    try {
      const res = await api.recognizeFood(formData)
      result.value = res.data
      recommendationTips.value = []
      message.success('识别成功 (Recognized Successfully)')
      currentStep.value = 2
      fetchAiAnalysis(res.data?.record_id)
    } catch (error) {
      message.error(error?.message || '请求出错')
    } finally {
      loading.value = false
    }
  }

  const handleUpload = async ({ file, onFinish, onError }) => {
    if (!ensureProfileComplete('上传识别')) {
      onError?.()
      return
    }

    loading.value = true
    result.value = null
    recommendationTips.value = []

    const formData = new FormData()
    formData.append('file', file.file)

    try {
      const res = await api.recognizeFood(formData)
      result.value = res.data
      recommendationTips.value = []
      message.success('识别成功 (Recognized Successfully)')
      currentStep.value = 2
      fetchAiAnalysis(res.data?.record_id)
      onFinish?.()
    } catch (error) {
      message.error(error?.message || '请求出错')
      onError?.()
    } finally {
      loading.value = false
    }
  }

  const goToStep = (step) => {
    if (step > 1 && !ensureProfileComplete('使用食物识别分析')) return
    if (!result.value && step > 1) {
      currentStep.value = 1
      return
    }
    if (step === 3 && safeDetails.value.length === 0) {
      message.warning('暂无可分析的识别结果')
      return
    }
    if (step === 4) {
      loadRecommendation()
    }
    currentStep.value = step
  }

  const getImageUrl = (path) => {
    if (!path) return ''
    if (/^https?:\/\//.test(path)) return path
    return path
  }

  onMounted(async () => {
    await userStore.getUserInfo().catch(() => null)
    if (!isProfileComplete.value) promptCompleteProfile('使用食物识别分析')
  })

  return {
    aiAnalysis,
    aiAnalysisLoading,
    currentNutrition,
    currentStep,
    fetchAiAnalysis,
    getImageUrl,
    goToStep,
    handleUpload,
    isProfileComplete,
    loadRecommendation,
    loading,
    mappedDetails,
    onRemove,
    primaryDetail,
    primaryFood,
    recommendationLoading,
    recommendationTips,
    resetWizard,
    result,
    safeDetails,
    showEncyclopedia,
    stepStatus,
    uploadByRawFile,
  }
}
