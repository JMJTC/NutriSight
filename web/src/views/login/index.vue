<template>
  <AppPage :show-footer="true" bg-cover :style="{ backgroundImage: `url(${bgImg})` }">
    <div
      style="transform: translateY(25px)"
      class="m-auto max-w-1500 min-w-345 f-c-c rounded-10 bg-white bg-opacity-60 p-15 card-shadow"
      dark:bg-dark
    >
      <div hidden w-380 px-20 py-35 md:block>
        <icon-custom-front-page pt-10 text-300 color-primary></icon-custom-front-page>
      </div>

      <div w-320 flex-col px-20 py-35>
        <h5 f-c-c text-24 font-normal color="#6a6a6a">
          <icon-custom-logo mr-10 text-50 color-primary />{{ $t('app_name') }}
        </h5>
        
        <n-tabs type="line" animated mt-20 v-model:value="activeTab">
          <n-tab-pane name="login" tab="登录">
            <div mt-20>
              <n-input
                v-model:value="loginInfo.username"
                autofocus
                class="h-50 items-center pl-10 text-16"
                placeholder="用户名"
                :maxlength="20"
              />
            </div>
            <div mt-20>
              <n-input
                v-model:value="loginInfo.password"
                class="h-50 items-center pl-10 text-16"
                type="password"
                show-password-on="mousedown"
                placeholder="密码"
                :maxlength="20"
                @keypress.enter="handleLogin"
              />
            </div>
            <div mt-20>
              <n-button
                h-50
                w-full
                rounded-5
                text-16
                type="primary"
                :loading="loading"
                @click="handleLogin"
              >
                {{ $t('views.login.text_login') }}
              </n-button>
            </div>
          </n-tab-pane>
          
          <n-tab-pane name="register" tab="注册">
            <div mt-20>
              <n-input
                v-model:value="registerInfo.username"
                class="h-50 items-center pl-10 text-16"
                placeholder="用户名 (至少3个字符)"
                :maxlength="20"
              />
            </div>
            <div mt-20>
              <n-input
                v-model:value="registerInfo.email"
                class="h-50 items-center pl-10 text-16"
                placeholder="邮箱"
              />
            </div>
            <div mt-20>
              <n-input
                v-model:value="registerInfo.password"
                class="h-50 items-center pl-10 text-16"
                type="password"
                show-password-on="mousedown"
                placeholder="密码 (至少6个字符)"
                :maxlength="20"
              />
            </div>
            <div mt-20>
              <n-input
                v-model:value="registerInfo.confirmPassword"
                class="h-50 items-center pl-10 text-16"
                type="password"
                show-password-on="mousedown"
                placeholder="确认密码"
                :maxlength="20"
                @keypress.enter="handleRegister"
              />
            </div>
            <div mt-20>
              <n-button
                h-50
                w-full
                rounded-5
                text-16
                type="primary"
                :loading="loading"
                @click="handleRegister"
              >
                立即注册
              </n-button>
            </div>
          </n-tab-pane>
        </n-tabs>
      </div>
    </div>
  </AppPage>
</template>

<script setup>
import { lStorage, setToken } from '@/utils'
import bgImg from '@/assets/images/login_bg.webp'
import api from '@/api'
import { addDynamicRoutes } from '@/router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { query } = useRoute()
const { t } = useI18n({ useScope: 'global' })

const activeTab = ref('login')
const loading = ref(false)

const loginInfo = ref({
  username: '',
  password: '',
})

const registerInfo = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

initLoginInfo()

function initLoginInfo() {
  const localLoginInfo = lStorage.get('loginInfo')
  if (localLoginInfo) {
    loginInfo.value.username = localLoginInfo.username || ''
    loginInfo.value.password = localLoginInfo.password || ''
  }
}

async function handleLogin() {
  const { username, password } = loginInfo.value
  if (!username || !password) {
    $message.warning(t('views.login.message_input_username_password'))
    return
  }
  try {
    loading.value = true
    $message.loading(t('views.login.message_verifying'))
    const res = await api.login({ username, password: password.toString() })
    $message.success(t('views.login.message_login_success'))
    setToken(res.data.access_token)
    await addDynamicRoutes()
    if (query.redirect) {
      const path = query.redirect
      Reflect.deleteProperty(query, 'redirect')
      router.push({ path, query })
    } else {
      router.push('/')
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  const { username, email, password, confirmPassword } = registerInfo.value
  
  if (!username || !email || !password || !confirmPassword) {
    $message.warning('请填写所有必填项')
    return
  }
  
  if (username.length < 3) {
    $message.warning('用户名至少需要3个字符')
    return
  }
  
  if (password.length < 6) {
    $message.warning('密码至少需要6个字符')
    return
  }
  
  if (password !== confirmPassword) {
    $message.warning('两次输入的密码不一致')
    return
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    $message.warning('请输入有效的邮箱地址')
    return
  }

  try {
    loading.value = true
    const res = await api.register({ username, email, password })
    if (res.code === 200) {
      $message.success('注册成功，请登录')
      activeTab.value = 'login'
      loginInfo.value.username = username
      loginInfo.value.password = ''
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>
