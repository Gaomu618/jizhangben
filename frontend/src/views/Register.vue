<template>
  <div class="register-page app-bg">
    <!-- 背景装饰：与 Login 形成系列（径向光晕位置对称呼应） -->
    <div class="bg-glow-left" aria-hidden="true"></div>
    <div class="bg-grid" aria-hidden="true"></div>

    <div class="register-wrap">
      <BaseEyebrow tone="accent">No.02 · Onboard · 注册</BaseEyebrow>

      <!-- Hero：1+3 布局，左侧标题 + 右侧 metric 卡（镜像 Login） -->
      <header class="hero">
        <div class="hero-text">
          <h1 class="hero-title display">
            开<em>新账</em>，<br />
            <span class="hero-sub">从一笔开始记录</span>
          </h1>
          <p class="hero-desc">
            三个字段、<em>三十秒</em>完成注册。
            我们只存必要信息 —— 邮箱用于密码找回，不会用于群发。
          </p>
        </div>

        <!-- 装饰性 SVG：注册流程示意（功能性装饰：3 步骤可视化） -->
        <div class="hero-steps">
          <div v-for="(s, i) in steps" :key="i" class="step" :class="{ 'is-active': i + 1 <= stepReached, 'is-current': i + 1 === stepReached }">
            <span class="step-num numeric">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="step-label">{{ s }}</span>
          </div>
        </div>
      </header>

      <!-- 注册表单卡片 -->
      <BaseCard padding="lg" class="form-card">
        <BaseSectionHeader
          eyebrow="Credentials · 凭据"
          eyebrow-tone="default"
          title="创建账号"
          subtitle="用户名、邮箱、密码 — 三步完成。"
        />

        <!-- 错误/成功提示 -->
        <div v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>
        <div v-if="successMsg" class="alert alert-success">{{ successMsg }}</div>

        <form @submit.prevent="handleRegister" class="form" novalidate>
          <div class="form-grid">
            <!-- 用户名（占 1 列，跨度 2/3） -->
            <div class="field-wide">
              <BaseInput
                v-model="form.username"
                label="用户名"
                placeholder="至少 3 位"
                :error="usernameError"
                :hint="usernameHint"
                autocomplete="username"
                @input="onUsernameInput"
              >
                <template #prefix>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.6"/>
                    <path d="M4 20c1.5-4 5-6 8-6s6.5 2 8 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                  </svg>
                </template>
              </BaseInput>
            </div>

            <!-- 邮箱 -->
            <div class="field-wide">
              <BaseInput
                v-model="form.email"
                type="email"
                label="邮箱"
                placeholder="example@mail.com"
                :error="emailError"
                :hint="emailHint"
                autocomplete="email"
                @input="onEmailInput"
              >
                <template #prefix>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.6"/>
                    <path d="M3 7l9 6 9-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </template>
              </BaseInput>
            </div>

            <!-- 密码 + 确认密码（2 列网格：1+1） -->
            <div class="field-half">
              <BaseInput
                v-model="form.password"
                type="password"
                label="密码"
                placeholder="至少 6 位"
                :error="passwordError"
                :hint="passwordHint"
                autocomplete="new-password"
                @input="onPasswordInput"
              >
                <template #prefix>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <rect x="4" y="10" width="16" height="10" rx="2" stroke="currentColor" stroke-width="1.6"/>
                    <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                  </svg>
                </template>
              </BaseInput>
            </div>
            <div class="field-half">
              <BaseInput
                v-model="form.confirmPassword"
                type="password"
                label="确认密码"
                placeholder="再次输入"
                :error="confirmError"
                :hint="confirmHint"
                autocomplete="new-password"
                @input="onConfirmInput"
              >
                <template #prefix>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M12 2a5 5 0 0 0-5 5v3H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-2V7a5 5 0 0 0-5-5z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                    <circle cx="12" cy="15" r="1.5" fill="currentColor"/>
                  </svg>
                </template>
              </BaseInput>
            </div>
          </div>

          <!-- 条款 -->
          <label class="terms">
            <input v-model="agreeTerms" type="checkbox" class="terms-input" />
            <span>我已阅读并同意 <a href="#" class="text-accent">服务条款</a> 与 <a href="#" class="text-accent">隐私政策</a></span>
          </label>

          <BaseButton type="submit" variant="accent" size="xl" :loading="loading" :disabled="!isFormValid" block>
            创建账号
          </BaseButton>
        </form>

        <p class="footer-link">
          已有账号？
          <router-link to="/login" class="text-accent">立即登录 →</router-link>
        </p>
      </BaseCard>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api'
import { BaseButton, BaseCard, BaseInput, BaseEyebrow, BaseSectionHeader } from '../components/base'

const router = useRouter()
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const agreeTerms = ref(false)

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// 校验状态
const usernameValid = computed(() => form.username.length >= 3)
const emailValid = computed(() => emailRegex.test(form.email))
const passwordValid = computed(() => form.password.length >= 6)
const confirmValid = computed(() => form.confirmPassword === form.password && form.confirmPassword.length > 0)
const isFormValid = computed(() => usernameValid.value && emailValid.value && passwordValid.value && confirmValid.value && agreeTerms.value)

// 步骤进度
const stepReached = computed(() => {
  if (usernameValid.value && emailValid.value && passwordValid.value && confirmValid.value) return 3
  if (usernameValid.value && emailValid.value) return 2
  if (usernameValid.value) return 1
  return 0
})
const steps = ['填写用户名', '验证邮箱', '设置密码']

// 错误/提示
const usernameError = ref('')
const usernameHint = ref('用户名至少 3 位')
const emailError = ref('')
const emailHint = ref('请输入有效邮箱')
const passwordError = ref('')
const passwordHint = ref('密码至少 6 位')
const confirmError = ref('')
const confirmHint = ref('两次密码需一致')

function onUsernameInput() {
  usernameError.value = ''
  if (!form.username) { usernameHint.value = '用户名至少 3 位' }
  else if (form.username.length < 3) { usernameHint.value = `还需 ${3 - form.username.length} 位` }
  else { usernameHint.value = '✓ 格式正确' }
}
function onEmailInput() {
  emailError.value = ''
  if (!form.email) { emailHint.value = '请输入有效邮箱' }
  else if (!emailRegex.test(form.email)) { emailHint.value = '邮箱格式不正确' }
  else { emailHint.value = '✓ 格式正确' }
}
function onPasswordInput() {
  passwordError.value = ''
  if (!form.password) { passwordHint.value = '密码至少 6 位' }
  else if (form.password.length < 6) { passwordHint.value = `还需 ${6 - form.password.length} 位` }
  else { passwordHint.value = '✓ 格式正确' }
  // 同步确认密码的提示
  if (form.confirmPassword) onConfirmInput()
}
function onConfirmInput() {
  confirmError.value = ''
  if (!form.confirmPassword) { confirmHint.value = '两次密码需一致' }
  else if (form.confirmPassword !== form.password) { confirmHint.value = '✗ 两次密码不一致' }
  else { confirmHint.value = '✓ 密码一致' }
}

async function handleRegister() {
  errorMsg.value = ''
  successMsg.value = ''
  if (!isFormValid.value) return
  loading.value = true
  try {
    await authAPI.register({ username: form.username, email: form.email, password: form.password })
    successMsg.value = '注册成功！即将跳转到登录页...'
    setTimeout(() => router.push('/login'), 1500)
  } catch (error) {
    errorMsg.value = error.message || '注册失败，请重试'
  } finally { loading.value = false }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  position: relative;
  overflow: hidden;
}

.bg-glow-left {
  position: absolute;
  top: -150px;
  left: -200px;
  width: 550px;
  height: 550px;
  background: radial-gradient(circle, rgba(29, 58, 138, 0.06) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.register-wrap {
  width: 100%;
  max-width: 540px;
  position: relative;
  z-index: 1;
}

/* ============== Hero：1+3 不对称（镜像 Login）============== */
.hero {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 24px;
  align-items: end;
  margin-bottom: 16px;
}

.hero-title {
  font-size: clamp(36px, 5vw, 48px);
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
}
.hero-title em { font-style: italic; color: var(--color-action-accent); font-weight: 700; }
.hero-sub { font-family: var(--font-display); font-weight: 400; color: var(--color-text-secondary); }

.hero-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  max-width: 320px;
}
.hero-desc em { font-style: italic; color: var(--color-action-accent); font-weight: 500; }

/* 步骤进度（功能性装饰：把"3 步"做成可视化导航） */
.hero-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
  font-size: 12px;
}
.step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--paper-200);
  color: var(--color-text-muted);
  transition: all var(--t-base) var(--ease-out);
  min-width: 140px;
}
.step-num { font-weight: 700; font-size: 11px; opacity: 0.5; }
.step-label { font-weight: 500; }
.step.is-active { background: var(--orange-50); color: var(--color-action-accent); }
.step.is-current { background: var(--color-action-accent); color: var(--color-text-inverse); transform: translateX(-4px); }
.step.is-current .step-num { opacity: 0.7; }

/* ============== 表单卡片 ============== */
.form-card { margin-top: 12px; }

.form { display: flex; flex-direction: column; gap: 16px; margin-top: 8px; }

/* 1+2 网格：用户名/邮箱独占一行，密码/确认各半行 */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.field-wide { grid-column: 1 / -1; }
.field-half { grid-column: span 1; }

.terms {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}
.terms-input {
  width: 16px;
  height: 16px;
  accent-color: var(--color-action-accent);
  cursor: pointer;
}

.text-accent {
  color: var(--color-action-accent);
  text-decoration: none;
  font-weight: 500;
}
.text-accent:hover { text-decoration: underline; }

.footer-link {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 16px;
}

/* 提示框 */
.alert {
  padding: 10px 14px;
  border-radius: var(--input-radius);
  font-size: 13px;
  margin-bottom: 4px;
}
.alert-error {
  background: var(--orange-50);
  border: 1px solid #f5c5a8;
  color: #b53d12;
}
.alert-success {
  background: var(--green-50);
  border: 1px solid #a7e3c3;
  color: var(--color-feedback-positive);
}

@media (max-width: 540px) {
  .hero { grid-template-columns: 1fr; gap: 12px; }
  .hero-steps { align-items: flex-start; }
  .form-grid { grid-template-columns: 1fr; }
  .field-half { grid-column: 1 / -1; }
}
</style>
