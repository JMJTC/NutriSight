<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NTabPane,
  NTabs,
  NImage,
  NUpload,
  NSpace,
  NSelect,
  NInputNumber,
} from 'naive-ui'
import { useI18n } from 'vue-i18n'
import CommonPage from '@/components/page/CommonPage.vue'
import { useUserStore } from '@/store'
import api from '@/api'

const { t } = useI18n()
const userStore = useUserStore()
const isLoading = ref(false)

const avatarUrl = computed(() => {
  if (!userStore.userInfo.avatar) return 'https://avatars.githubusercontent.com/u/54677442?v=4'
  if (userStore.userInfo.avatar.startsWith('http')) return userStore.userInfo.avatar
  const backendHost = import.meta.env.VITE_APP_API_BASE_URL || 'http://127.0.0.1:9999'
  return `${backendHost}${userStore.userInfo.avatar}`
})

async function handleAvatarUpload({ file }) {
  const formData = new FormData()
  formData.append('file', file.file)

  try {
    isLoading.value = true
    const res = await api.updateAvatar(formData)
    if (res.code === 200) {
      $message.success('头像上传成功')
      userStore.setUserInfo({ avatar: res.data.avatar })
      infoForm.value.avatar = res.data.avatar
    }
  } catch (error) {
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

async function restoreDefaultAvatar() {
  try {
    isLoading.value = true
    // 这里简单地清空头像路径，后端可以处理为恢复默认
    await api.updateProfile({ ...infoForm.value, avatar: null })
    userStore.setUserInfo({ avatar: null })
    infoForm.value.avatar = null
    $message.success('已恢复默认头像')
  } catch (error) {
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

// 用户信息的表单
const infoFormRef = ref(null)
const infoForm = ref({
  avatar: userStore.userInfo.avatar,
  username: userStore.name,
  email: userStore.email,
  height_cm: userStore.userInfo.height_cm,
  weight_kg: userStore.userInfo.weight_kg,
  gender: userStore.userInfo.gender,
  age: userStore.userInfo.age,
})

const refreshProfileForm = async () => {
  const data = await userStore.getUserInfo()
  if (!data || data instanceof Error) return
  const weightKg = Number(data.weight_kg)
  infoForm.value = {
    ...infoForm.value,
    avatar: data.avatar,
    username: data.username,
    email: data.email,
    height_cm: data.height_cm,
    weight_kg: Number.isFinite(weightKg) ? weightKg : null,
    gender: data.gender,
    age: data.age,
  }
}

onMounted(async () => {
  if (!userStore.userId) {
    await refreshProfileForm()
  }
})

const genderOptions = [
  { label: '男', value: 1 },
  { label: '女', value: 2 },
  { label: '其他', value: 3 },
]

const isFormInvalid = computed(() => {
  const { username, email, height_cm, weight_kg, gender, age } = infoForm.value
  return (
    !username ||
    !email ||
    height_cm === null ||
    height_cm < 130 ||
    height_cm > 250 ||
    weight_kg === null ||
    weight_kg < 30 ||
    weight_kg > 200 ||
    gender === null ||
    age === null ||
    age < 1 ||
    age > 120
  )
})

async function updateProfile() {
  isLoading.value = true
  infoFormRef.value?.validate(async (err) => {
    if (err) {
      isLoading.value = false
      return
    }
    await api
      .updateProfile({ ...infoForm.value })
      .then(() => {
        userStore.setUserInfo(infoForm.value)
        isLoading.value = false
        $message.success(t('common.text.update_success'))
      })
      .catch(() => {
        isLoading.value = false
      })
  })
}
const infoFormRules = {
  username: [
    {
      required: true,
      message: t('views.profile.message_username_required'),
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: true,
      message: t('views.profile.message_email_required'),
      trigger: ['input', 'blur'],
    },
  ],
  height_cm: [
    {
      required: true,
      type: 'number',
      message: '请输入130-250之间的整数',
      trigger: ['input', 'blur'],
    },
    {
      validator: (rule, value) => value >= 130 && value <= 250,
      message: '请输入130-250之间的整数',
      trigger: ['input', 'blur'],
    },
  ],
  weight_kg: [
    {
      required: true,
      type: 'number',
      message: '请输入30.0-200.0之间的数值',
      trigger: ['input', 'blur'],
    },
    {
      validator: (rule, value) => value >= 30 && value <= 200,
      message: '请输入30.0-200.0之间的数值',
      trigger: ['input', 'blur'],
    },
  ],
  gender: [
    {
      required: true,
      type: 'number',
      message: '请选择性别',
      trigger: ['blur', 'change'],
    },
  ],
  age: [
    {
      required: true,
      type: 'number',
      message: '请输入1-120之间的整数',
      trigger: ['input', 'blur'],
    },
    {
      validator: (rule, value) => value >= 1 && value <= 120,
      message: '请输入1-120之间的整数',
      trigger: ['input', 'blur'],
    },
  ],
}

// 修改密码的表单
const passwordFormRef = ref(null)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

async function updatePassword() {
  isLoading.value = true
  passwordFormRef.value?.validate(async (err) => {
    if (!err) {
      const data = { ...passwordForm.value }
      await api
        .updatePassword(data)
        .then((res) => {
          $message.success(res.msg)
          passwordForm.value = {
            old_password: '',
            new_password: '',
            confirm_password: '',
          }
          isLoading.value = false
        })
        .catch(() => {
          isLoading.value = false
        })
    }
  })
}
const passwordFormRules = {
  old_password: [
    {
      required: true,
      message: t('views.profile.message_old_password_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  new_password: [
    {
      required: true,
      message: t('views.profile.message_new_password_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirm_password: [
    {
      required: true,
      message: t('views.profile.message_password_confirmation_required'),
      trigger: ['input', 'blur'],
    },
    {
      validator: validatePasswordStartWith,
      message: t('views.profile.message_password_confirmation_diff'),
      trigger: 'input',
    },
    {
      validator: validatePasswordSame,
      message: t('views.profile.message_password_confirmation_diff'),
      trigger: ['blur', 'password-input'],
    },
  ],
}
function validatePasswordStartWith(rule, value) {
  return (
    !!passwordForm.value.new_password &&
    passwordForm.value.new_password.startsWith(value) &&
    passwordForm.value.new_password.length >= value.length
  )
}
function validatePasswordSame(rule, value) {
  return value === passwordForm.value.new_password
}
</script>

<template>
  <CommonPage :show-header="false">
    <NTabs type="line" animated>
      <NTabPane name="website" :tab="$t('views.profile.label_modify_information')">
        <div class="m-30 flex items-center">
          <NForm
            ref="infoFormRef"
            label-placement="left"
            label-align="left"
            label-width="100"
            :model="infoForm"
            :rules="infoFormRules"
            class="w-400"
          >
            <NFormItem :label="$t('views.profile.label_avatar')" path="avatar">
              <NSpace align="center">
                <NImage
                  width="100"
                  height="100"
                  class="overflow-hidden rounded-full"
                  :src="avatarUrl"
                ></NImage>
                <NUpload
                  :show-file-list="false"
                  accept="image/*"
                  :custom-request="handleAvatarUpload"
                  @before-upload="
                    (data) => {
                      const file = data.file.file
                      if (file.size > 2 * 1024 * 1024) {
                        $message.error('图片不能超过 2MB')
                        return false
                      }
                      return true
                    }
                  "
                >
                  <NButton type="primary" size="small">上传新头像</NButton>
                </NUpload>
                <NButton type="default" size="small" @click="restoreDefaultAvatar"
                  >恢复默认</NButton
                >
              </NSpace>
            </NFormItem>
            <NFormItem :label="$t('views.profile.label_username')" path="username">
              <NInput
                v-model:value="infoForm.username"
                type="text"
                :placeholder="$t('views.profile.placeholder_username')"
              />
            </NFormItem>
            <NFormItem :label="$t('views.profile.label_email')" path="email">
              <NInput
                v-model:value="infoForm.email"
                type="text"
                :placeholder="$t('views.profile.placeholder_email')"
              />
            </NFormItem>

            <NFormItem label="身高(cm)" path="height_cm">
              <NInputNumber
                v-model:value="infoForm.height_cm"
                :min="130"
                :max="250"
                :precision="0"
                placeholder="请输入130-250之间的整数"
                class="w-full"
              />
            </NFormItem>

            <NFormItem label="体重(kg)" path="weight_kg">
              <NInputNumber
                v-model:value="infoForm.weight_kg"
                :min="30"
                :max="200"
                :precision="1"
                placeholder="请输入30.0-200.0之间的数值"
                class="w-full"
              />
            </NFormItem>

            <NFormItem label="性别" path="gender">
              <NSelect
                v-model:value="infoForm.gender"
                :options="genderOptions"
                placeholder="请选择性别"
              />
            </NFormItem>

            <NFormItem label="年龄" path="age">
              <NInputNumber
                v-model:value="infoForm.age"
                :min="1"
                :max="120"
                :precision="0"
                placeholder="请输入1-120之间的整数"
                class="w-full"
              />
            </NFormItem>

            <NButton
              type="primary"
              :loading="isLoading"
              :disabled="isFormInvalid"
              @click="updateProfile"
            >
              {{ isFormInvalid ? '请完善必填信息' : $t('common.buttons.update') }}
            </NButton>
          </NForm>
        </div>
      </NTabPane>
      <NTabPane name="contact" :tab="$t('views.profile.label_change_password')">
        <NForm
          ref="passwordFormRef"
          label-placement="left"
          label-align="left"
          :model="passwordForm"
          label-width="200"
          :rules="passwordFormRules"
          class="m-30 w-500"
        >
          <NFormItem :label="$t('views.profile.label_old_password')" path="old_password">
            <NInput
              v-model:value="passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_old_password')"
            />
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_new_password')" path="new_password">
            <NInput
              v-model:value="passwordForm.new_password"
              :disabled="!passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_new_password')"
            />
          </NFormItem>
          <NFormItem :label="$t('views.profile.label_confirm_password')" path="confirm_password">
            <NInput
              v-model:value="passwordForm.confirm_password"
              :disabled="!passwordForm.new_password"
              type="password"
              show-password-on="mousedown"
              :placeholder="$t('views.profile.placeholder_confirm_password')"
            />
          </NFormItem>
          <NButton type="primary" :loading="isLoading" @click="updatePassword">
            {{ $t('common.buttons.update') }}
          </NButton>
        </NForm>
      </NTabPane>
    </NTabs>
  </CommonPage>
</template>
