<template>
  <div class="login-page app-bg">
    <!-- 背景装饰：径向光晕（规范：20% 装饰配额） -->
    <div class="bg-glow" aria-hidden="true"></div>
    <div class="bg-grid" aria-hidden="true"></div>

    <div class="login-wrap">
      <!-- ============ Eyebrow 标签（NO.01 · AUTH · 登录） ============ -->
      <p class="eyebrow eyebrow-accent">No.01 · Auth · 登录</p>

      <!-- ============ 1+3 不对称布局：左侧大字 + 右侧统计 ============ -->
      <header class="hero">
        <div class="hero-text">
          <h1 class="hero-title display">
            <em>账本</em>，<br />
            <span class="hero-sub">记录每一次收支</span>
          </h1>
          <p class="hero-desc">
            每笔进账与花销，<em>清晰可视</em>。
            智能分类、预算提醒、回收站保护 —— 让记账回归本意。
          </p>
        </div>

        <!-- 装饰性 SVG sparkline：规范要求"数据卡都有装饰图表" -->
        <svg class="hero-spark" viewBox="0 0 220 60" fill="none" aria-hidden="true">
          <defs>
            <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#d94f1e" stop-opacity="0.18" />
              <stop offset="100%" stop-color="#d94f1e" stop-opacity="0" />
            </linearGradient>
          </defs>
          <path d="M0 45 L25 38 L50 42 L75 30 L100 33 L125 22 L150 26 L175 14 L200 18 L220 8"
                stroke="#d94f1e" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <path d="M0 45 L25 38 L50 42 L75 30 L100 33 L125 22 L150 26 L175 14 L200 18 L220 8 L220 60 L0 60 Z"
                fill="url(#sparkGrad)"/>
          <circle cx="220" cy="8" r="3" fill="#d94f1e" />
        </svg>
      </header>

      <!-- ============ 深色引导卡：突出"今日支出"主指标 ============ -->
      <section class="hero-metric card-dark">
        <div class="metric-row">
          <div>
            <p class="metric-eyebrow">本月数据</p>
            <p class="metric-value numeric">¥<span class="num-big">5,714</span><span class="num-tail">.00</span></p>
            <p class="metric-trend">
              <span class="text-expense">↑ 12%</span>
              <span class="muted">较上周 · 主要来自餐饮</span>
            </p>
          </div>
          <div class="metric-side">
            <div class="mini-stat">
              <span class="mini-label">笔数</span>
              <span class="mini-value numeric">23</span>
            </div>
            <div class="mini-stat">
              <span class="mini-label">日均</span>
              <span class="mini-value numeric">¥184</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ============ 主登录卡片 ============ -->
      <section class="login-card card">
        <p class="eyebrow">Credentials · 凭据</p>
        <h2 class="form-title display">欢迎回来</h2>

        <!-- 错误提示 -->
        <div v-if="errorMsg" class="error-box">{{ errorMsg }}</div>

        <form @submit.prevent="handleLogin" class="form" novalidate>
          <div class="form-group">
            <label for="login-username" class="form-label">用户名</label>
            <div class="input-wrap">
              <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.6"/>
                <path d="M4 20c1.5-4 5-6 8-6s6.5 2 8 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
              <input
                id="login-username"
                v-model="form.username"
                type="text"
                placeholder="请输入用户名"
                class="form-input"
                @input="validateUsername"
                autocomplete="username"
                aria-describedby="username-tip"
              />
            </div>
            <p id="username-tip" class="form-tip" :class="usernameTipClass">{{ usernameTip }}</p>
          </div>

          <div class="form-group">
            <label for="login-password" class="form-label">密码</label>
            <div class="input-wrap">
              <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="4" y="10" width="16" height="10" rx="2" stroke="currentColor" stroke-width="1.6"/>
                <path d="M8 10V7a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
              <input
                id="login-password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                class="form-input"
                @input="validatePassword"
                autocomplete="current-password"
                aria-describedby="password-tip"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="toggle-eye"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              >
                <svg v-if="showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M3 3l18 18" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                  <path d="M10.5 6.5a4 4 0 0 0 5.7 5.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                  <path d="M9.9 5.1A10 10 0 0 1 12 5c5 0 9 4 10 7-0.3 1-1 2-2 3M6.6 6.6C4 8.3 2.4 10.7 2 12c1 3 5 7 10 7 1.5 0 3-0.4 4.3-1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/>
                </svg>
              </button>
            </div>
            <p id="password-tip" class="form-tip" :class="passwordTipClass">{{ passwordTip }}</p>
          </div>

          <div class="form-row">
            <label class="checkbox">
              <input v-model="form.remember" type="checkbox" class="checkbox-input" />
              <span>7 天内免登录</span>
            </label>
            <a href="#" class="text-muted hover-ink">忘记密码？</a>
          </div>

          <button type="submit" class="submit-btn btn-primary" :disabled="loading || !isFormValid">
            <span v-if="loading" class="spinner-white" aria-hidden="true"></span>
            <span v-else>登 录</span>
          </button>

          <div class="divider"><span>或</span></div>

          <button type="button" class="btn-wechat" @click="handleWechatLogin" :disabled="wechatLoading">
            <svg v-if="!wechatLoading" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M8.7 13.3c-.4 0-.8-.4-.8-.8s.4-.8.8-.8.8.4.8.8-.3.8-.8.8zm6.6 0c-.4 0-.8-.4-.8-.8s.4-.8.8-.8.8.4.8.8-.4.8-.8.8zM9 6c-3.9 0-7 2.5-7 5.6 0 1.7 1 3.3 2.5 4.4l-.6 2 2.3-1.2c.7.2 1.5.3 2.3.3l.7-.1c-.2-.6-.2-1.2-.2-1.8 0-3.1 3-5.6 6.7-5.6h.6C15.5 7.5 12.5 6 9 6zm10 8.4c0-2.5-2.5-4.5-5.5-4.5S8 11.9 8 14.4s2.5 4.5 5.5 4.5c.6 0 1.3-.1 1.8-.2l1.9 1-.5-1.6c1.4-.8 2.3-2.1 2.3-3.7z"/>
            </svg>
            <span v-if="wechatLoading" class="spinner-white" aria-hidden="true"></span>
            <span v-else>微信一键登录</span>
          </button>
        </form>

        <p class="footer-link">
          还没有账号？
          <router-link to="/register" class="text-accent">立即注册 →</router-link>
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '../api'
import { useAuth } from '../stores/auth'
import { t } from '../i18n'

const router = useRouter()
const { setAuth } = useAuth()

const form = reactive({ username: '', password: '', remember: false })
const loading = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)
const wechatLoading = ref(false)
const usernameTip = ref('用户名至少 3 位')
const passwordTip = ref('密码至少 6 位')
const usernameTipClass = ref('muted')
const passwordTipClass = ref('muted')

const isFormValid = computed(
  () => form.username.length >= 3 && form.password.length >= 6
)

function validateUsername() {
  const len = form.username.length
  if (len === 0) { usernameTip.value = '用户名至少 3 位'; usernameTipClass.value = 'muted' }
  else if (len < 3) { usernameTip.value = `还需 ${3 - len} 位`; usernameTipClass.value = 'warn' }
  else { usernameTip.value = '✓ 已就绪'; usernameTipClass.value = 'success' }
}

function validatePassword() {
  const len = form.password.length
  if (len === 0) { passwordTip.value = '密码至少 6 位'; passwordTipClass.value = 'muted' }
  else if (len < 6) { passwordTip.value = `还需 ${6 - len} 位`; passwordTipClass.value = 'warn' }
  else { passwordTip.value = '✓ 已就绪'; passwordTipClass.value = 'success' }
}

async function handleLogin() {
  errorMsg.value = ''
  if (!isFormValid.value) return
  loading.value = true
  try {
    const res = await authAPI.login({ username: form.username, password: form.password })
    // 后端 /api/auth/login 必然返回真 token；如果没有就是接口异常
    if (!res.data.token) {
      throw new Error('登录响应缺少 token，请重试')
    }
    setAuth(res.data.token, res.data.userinfo)
    router.push('/')
  } catch (error) {
    errorMsg.value = error.message || '登录失败，请检查账号密码'
  } finally { loading.value = false }
}

async function handleWechatLogin() {
  wechatLoading.value = true
  errorMsg.value = ''
  try {
    let code
    if (typeof wx !== 'undefined' && wx.login) {
      code = await new Promise((resolve, reject) => {
        wx.login({ success: (res) => resolve(res.code), fail: reject })
      })
    } else if (typeof uni !== 'undefined' && uni.login) {
      code = await new Promise((resolve, reject) => {
        uni.login({ provider: 'weixin', success: (res) => resolve(res.code), fail: reject })
      })
    } else {
      code = 'dev_test_code_' + Date.now()
    }
    const res = await authAPI.wechatLogin({ code })
    setAuth(res.data.token, res.data.userinfo)
    router.push('/')
  } catch (error) {
    errorMsg.value = error.message || '微信登录失败'
  } finally { wechatLoading.value = false }
}
</script>

<style scoped>
/* ==================== 页面：暖底 + 径向光晕 ==================== */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  position: relative;
  overflow: hidden;
}

.bg-glow {
  position: absolute;
  top: -200px;
  right: -200px;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(217, 79, 30, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(15, 23, 42, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 23, 42, 0.025) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
  pointer-events: none;
}

.login-wrap {
  width: 100%;
  max-width: 440px;
  position: relative;
  z-index: 1;
}

/* ==================== Hero：1+3 不对称 ==================== */
.hero {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
  align-items: end;
  margin: 0 0 12px;
}

.hero-title {
  font-size: clamp(36px, 5vw, 48px);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}
.hero-title em {
  font-style: italic;
  color: var(--color-action-accent);
  font-weight: 700;
}
.hero-sub {
  font-family: var(--font-display);
  font-weight: 400;
  color: var(--color-text-secondary);
}

.hero-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  max-width: 360px;
}
.hero-desc em {
  font-style: italic;
  color: var(--color-action-accent);
  font-weight: 500;
}

.hero-spark {
  width: 100%;
  height: 60px;
  align-self: end;
}

/* ==================== 深色引导卡：Hero metric ==================== */
.card-dark {
  background: var(--color-bg-deep);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--card-radius);
  padding: 24px;
  box-shadow: var(--shadow-lg);
  margin-bottom: 24px;
}

.metric-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.metric-eyebrow {
  font-family: var(--font-num);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--paper-200);
  opacity: 0.7;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 36px;
  font-weight: 600;
  letter-spacing: -0.03em;
  line-height: 1;
  color: var(--paper-50);
  margin-bottom: 6px;
}
.num-tail { font-size: 22px; opacity: 0.6; }

.metric-trend {
  font-size: 12px;
  color: var(--paper-200);
  opacity: 0.85;
}
.metric-trend .text-expense {
  color: var(--orange-500);
  font-weight: 600;
  margin-right: 6px;
}
.metric-trend .muted { opacity: 0.55; }

.metric-side {
  display: flex;
  gap: 14px;
}
.mini-stat {
  text-align: right;
}
.mini-label {
  display: block;
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--paper-200);
  opacity: 0.6;
  margin-bottom: 2px;
}
.mini-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--paper-50);
}

/* ==================== 主登录卡片 ==================== */
.login-card {
  padding: 32px;
}

.form-title {
  font-size: 22px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 8px 0 24px;
}

.error-box {
  background: var(--orange-50);
  border: 1px solid #f5c5a8;
  color: #b53d12;
  padding: 10px 12px;
  border-radius: var(--input-radius);
  font-size: 13px;
  margin-bottom: 16px;
}

/* ==================== 表单 ==================== */
.form-group { margin-bottom: 18px; }

.form-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.input-wrap {
  display: flex;
  align-items: center;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--input-radius);
  padding: 0 12px;
  transition: all var(--t-fast) var(--ease-out);
}
.input-wrap:focus-within {
  border-color: var(--color-action-accent);
  box-shadow: 0 0 0 3px rgba(217, 79, 30, 0.12);
  background: white;
}

.input-icon {
  color: var(--color-text-muted);
  margin-right: 10px;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 12px 0;
  font-size: 15px;
  font-family: inherit;
  background: transparent;
  color: var(--color-text-primary);
}
.form-input::placeholder { color: var(--color-text-muted); }

.toggle-eye {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 6px;
  display: inline-flex;
  border-radius: 6px;
  transition: color var(--t-fast) var(--ease-out);
}
.toggle-eye:hover { color: var(--color-text-primary); }

.form-tip { font-size: 11px; margin-top: 5px; min-height: 14px; }
.form-tip.muted { color: var(--color-text-muted); }
.form-tip.warn { color: var(--color-action-accent); }
.form-tip.success { color: var(--color-feedback-positive); }

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  font-size: 13px;
}
.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-secondary);
  cursor: pointer;
  user-select: none;
}
.checkbox-input {
  width: 16px;
  height: 16px;
  accent-color: var(--color-action-accent);
  cursor: pointer;
}
.hover-ink { text-decoration: none; transition: color var(--t-fast) var(--ease-out); }
.hover-ink:hover { color: var(--color-text-primary); }

/* ==================== 按钮 ==================== */
.submit-btn {
  width: 100%;
  padding: 14px;
  font-size: 15px;
  letter-spacing: 0.05em;
}

.divider {
  display: flex;
  align-items: center;
  margin: 18px 0;
  color: var(--color-text-muted);
  font-size: 11px;
  letter-spacing: 0.2em;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border-soft);
}
.divider span { padding: 0 14px; }

.btn-wechat {
  width: 100%;
  background: var(--green-500);
  color: white;
  border: none;
  border-radius: var(--btn-radius);
  padding: 12px;
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: background var(--t-fast) var(--ease-out);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-wechat:hover { background: var(--green-700); }
.btn-wechat:disabled { opacity: 0.6; cursor: not-allowed; }

.spinner-white {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ==================== 底部 ==================== */
.footer-link {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 24px;
}
.text-accent {
  color: var(--color-action-accent);
  text-decoration: none;
  font-weight: 500;
  font-family: var(--font-display);
}
.text-accent:hover { text-decoration: underline; }

.muted { color: var(--color-text-muted); }

/* ==================== 响应式：窄屏折成 1 列 ==================== */
@media (max-width: 480px) {
  .hero { grid-template-columns: 1fr; gap: 8px; }
  .hero-spark { display: none; }
  .metric-row { flex-direction: column; align-items: flex-start; }
  .metric-side { width: 100%; justify-content: space-between; }
  .login-card { padding: 24px 20px; }
}
</style>
