<template>
  <div class="min-h-screen app-bg page-wrap">
    <!-- 顶部导航 -->
    <header class="nav">
      <div class="nav-inner">
        <div class="nav-left">
          <button class="icon-btn" @click="router.push('/')" :title="'返回'">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <h1 class="nav-title display">个人中心</h1>
        </div>
      </div>
    </header>

    <div class="page-content">
      <!-- 用户信息卡 -->
      <BaseCard padding="lg" class="profile-card">
        <!-- 头像 -->
        <div class="avatar-section">
          <div class="avatar-wrap" @click="triggerAvatarUpload">
            <img v-if="userInfo.avatar_url" :src="fullAvatarUrl" class="avatar-img" alt="avatar" />
            <div v-else class="avatar-placeholder">
              {{ userInfo.username ? userInfo.username.charAt(0).toUpperCase() : '?' }}
            </div>
            <div class="avatar-mask">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M3 7h4l2-3h6l2 3h4v13H3V7z" stroke="white" stroke-width="1.6" stroke-linejoin="round"/>
                <circle cx="12" cy="13" r="4" stroke="white" stroke-width="1.6"/>
              </svg>
              <span>更换</span>
            </div>
          </div>
          <input
            ref="avatarInput"
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            style="display: none"
            @change="onAvatarSelected"
          />
          <div class="user-meta">
            <h2 class="user-name display">{{ userInfo.nickname || userInfo.username || '未设置' }}</h2>
            <p class="user-handle">@{{ userInfo.username || 'anonymous' }}</p>
            <p v-if="userInfo.email" class="user-email micro">{{ userInfo.email }}</p>
          </div>
        </div>
      </BaseCard>

      <!-- 资料编辑 -->
      <BaseSectionHeader
        eyebrow="Profile · 资料"
        title="编辑资料"
        subtitle="昵称、头像 — 让账本更个性"
      />

      <BaseCard padding="md" class="form-card">
        <div class="form-group">
          <label class="form-label">昵称</label>
          <BaseInput
            v-model="form.nickname"
            placeholder="显示在账本上的名字"
            :hint="nicknameHint"
            :error="nicknameError"
            maxlength="20"
            @input="onNicknameInput"
          />
        </div>

        <div class="form-group">
          <label class="form-label">用户名（不可修改）</label>
          <BaseInput
            :value="userInfo.username"
            disabled
            hint="注册时设定，不支持修改"
          />
        </div>

        <div v-if="formError" class="alert alert-error">{{ formError }}</div>
        <div v-if="formSuccess" class="alert alert-success">{{ formSuccess }}</div>

        <div class="form-actions">
          <BaseButton
            variant="primary"
            :loading="submitting"
            :disabled="!isDirty"
            @click="saveProfile"
          >保存修改</BaseButton>
        </div>
      </BaseCard>

      <!-- 退出登录 -->
      <BaseSectionHeader
        class="mt-6"
        eyebrow="Session · 会话"
        title="退出"
      />
      <BaseCard padding="md">
        <div class="logout-row">
          <div>
            <p class="logout-title">退出登录</p>
            <p class="logout-hint">退出后会清除本地 token，需要重新登录</p>
          </div>
          <BaseButton variant="danger" @click="doLogout" :loading="loggingOut">退出</BaseButton>
        </div>
      </BaseCard>

      <p class="footer-tip">记账本财报分析系统 · v1.0</p>
    </div>

    <div class="tabbar-safe"></div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api'
import { useAuth } from '../stores/auth'
import {
  BaseButton, BaseCard, BaseInput,
  BaseEyebrow, BaseSectionHeader,
} from '../components/base'

const router = useRouter()
const { state: authState, clearAuth } = useAuth()

const loading = ref(false)
const submitting = ref(false)
const loggingOut = ref(false)
const avatarInput = ref(null)
const formError = ref('')
const formSuccess = ref('')
const nicknameError = ref('')
const nicknameHint = ref('20 字符以内，可不改')

const userInfo = reactive({
  id: null,
  username: '',
  nickname: '',
  email: '',
  avatar_url: '',
})

const form = reactive({
  nickname: '',
})

// 头像完整 URL（后端存的是相对路径 /uploads/...，走 vite 代理）
const fullAvatarUrl = computed(() => {
  if (!userInfo.avatar_url) return ''
  if (userInfo.avatar_url.startsWith('http')) return userInfo.avatar_url
  return userInfo.avatar_url  // 相对路径直接用，vite 代理 /uploads → 5002
})

const isDirty = computed(() => {
  return form.nickname !== (userInfo.nickname || '')
})

function onNicknameInput() {
  nicknameError.value = ''
  if (!form.nickname) {
    nicknameHint.value = '20 字符以内，可不改'
  } else if (form.nickname.length > 20) {
    nicknameError.value = '昵称不能超过 20 字符'
  } else {
    nicknameHint.value = '✓ 已就绪'
  }
}

async function loadUserInfo() {
  loading.value = true
  try {
    const res = await authAPI.getUserInfo()
    const info = res.data || {}
    Object.assign(userInfo, {
      id: info.id,
      username: info.username,
      nickname: info.nickname || '',
      email: info.email || '',
      avatar_url: info.avatar_url || '',
    })
    form.nickname = userInfo.nickname
  } catch (err) {
    console.error('加载用户信息失败', err)
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  formError.value = ''
  formSuccess.value = ''
  submitting.value = true
  try {
    await authAPI.updateProfile({ nickname: form.nickname })
    userInfo.nickname = form.nickname
    formSuccess.value = '✓ 已保存'
    setTimeout(() => { formSuccess.value = '' }, 2000)
  } catch (err) {
    formError.value = err.message || '保存失败'
  } finally {
    submitting.value = false
  }
}

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

async function onAvatarSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    formError.value = '图片过大（最大 2MB）'
    return
  }
  formError.value = ''
  formSuccess.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await authAPI.uploadAvatar(fd)
    userInfo.avatar_url = res.data.avatar_url
    formSuccess.value = '✓ 头像已更新'
    setTimeout(() => { formSuccess.value = '' }, 2000)
  } catch (err) {
    formError.value = err.message || '头像上传失败'
  } finally {
    // 重置 input，允许重复选同一文件
    e.target.value = ''
  }
}

async function doLogout() {
  if (!confirm('确定要退出登录吗？')) return
  loggingOut.value = true
  try {
    await authAPI.logout()
  } catch (e) {
    // 即便后端失败，也清本地（JWT 无状态）
  } finally {
    clearAuth()
    loggingOut.value = false
    router.push('/login')
  }
}

onMounted(loadUserInfo)
</script>

<style scoped>
/* 用 flexbox 强制居中（和 Budget.vue 保持一致） */
.page-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.page-content {
  width: 100%;
  max-width: 42rem;     /* 等同 max-w-2xl */
  padding: 0 16px 32px;
  box-sizing: border-box;
}

.nav {
  position: sticky; top: 0; z-index: 10;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #eee;
}
.nav-inner {
  width: 100%;
  max-width: 768px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex; align-items: center; gap: 10px;
  box-sizing: border-box;
}
.nav-left { display: flex; align-items: center; gap: 10px; }
.nav-title { font-size: 18px; font-weight: 600; margin: 0; }
.icon-btn {
  background: transparent; border: none; padding: 6px;
  border-radius: 8px; cursor: pointer; color: #555;
  display: inline-flex; align-items: center;
}
.icon-btn:hover { background: #f0f0f0; color: #111; }

.profile-card { margin-top: 16px; }
.avatar-section {
  display: flex; align-items: center; gap: 20px;
}
.avatar-wrap {
  position: relative; width: 80px; height: 80px;
  border-radius: 50%; overflow: hidden; cursor: pointer;
  flex-shrink: 0;
  background: linear-gradient(135deg, #d94f1e, #f5a073);
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 32px; font-weight: 600;
}
.avatar-mask {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.5); color: white;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 2px; font-size: 11px;
  opacity: 0; transition: opacity 0.2s;
}
.avatar-wrap:hover .avatar-mask { opacity: 1; }

.user-meta { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.user-name {
  font-size: 20px; font-weight: 600; margin: 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.user-handle { font-size: 13px; color: #888; margin: 0; }
.user-email { font-size: 12px; color: #999; margin: 0; }

.form-card { display: flex; flex-direction: column; gap: 16px; margin-top: 12px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label {
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase; color: #666;
}
.form-actions { display: flex; gap: 8px; justify-content: flex-end; }

.alert { padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.alert-error { background: #fff5f0; border: 1px solid #f5c5a8; color: #b53d12; }
.alert-success { background: #e8f5ed; border: 1px solid #a7e3c3; color: #2e7d4f; }

.logout-row {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.logout-title { font-size: 14px; font-weight: 500; margin: 0 0 4px; }
.logout-hint { font-size: 12px; color: #888; margin: 0; }

.footer-tip {
  text-align: center; font-size: 12px; color: #aaa;
  margin-top: 32px; padding: 16px 0;
}
.tabbar-safe { height: 32px; }
</style>
