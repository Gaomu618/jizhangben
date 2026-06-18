<template>
  <div class="min-h-screen app-bg page-wrap">
    <!-- 顶部导航 -->
    <header class="nav">
      <div class="nav-inner">
        <div class="nav-left">
          <button class="icon-btn" @click="router.push('/')" :title="t('nav.back', '返回')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="nav-icon"><IconBudget :size="22" /></span>
          <h1 class="nav-title display">预算管理</h1>
        </div>
        <div class="nav-actions">
          <button class="icon-btn" @click="router.push('/categories')" title="管理分类" aria-label="管理分类">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M3 6h18M3 12h18M3 18h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </button>
          <select :value="lang" @change="setLanguage($event.target.value)" class="lang-select-inline">
            <option v-for="l in SUPPORTED_LANGUAGES" :key="l.code" :value="l.code">{{ l.label }}</option>
          </select>
        </div>
      </div>
    </header>

    <div class="page-content">
      <!-- 月份选择 -->
      <BaseCard padding="md" class="mb-4">
        <BaseEyebrow tone="default">月份</BaseEyebrow>
        <div class="month-row">
          <button class="month-nav" @click="prevMonth">‹</button>
          <span class="month-label display">{{ year }}年{{ month }}月</span>
          <button class="month-nav" @click="nextMonth">›</button>
        </div>
        <div class="month-tools">
          <button class="tool-btn" @click="goCurrentMonth" :disabled="isCurrentMonth" title="回到当月">📅 当月</button>
          <button class="tool-btn" @click="forceRefresh" :disabled="loading" title="强制刷新">🔄 刷新</button>
        </div>
        <p v-if="lastUpdatedAt" class="last-update">最近更新：{{ lastUpdatedAt }}</p>
      </BaseCard>

      <!-- 预算列表 -->
      <BaseSectionHeader
        eyebrow="Budget · 预算"
        title="分类预算"
        :subtitle="`共 ${budgetList.length} 个分类`"
      />

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中…</span>
      </div>

      <BaseEmpty
        v-else-if="budgetList.length === 0"
        title="还没有设置预算"
        message="点击下方「+ 添加预算」开始管理你的开支"
      />

      <div v-else class="budget-cards">
        <BaseCard
          v-for="b in budgetList"
          :key="b.category"
          padding="md"
          class="budget-card"
        >
          <div class="budget-head">
            <div class="budget-info">
              <span class="budget-cat display">{{ b.category }}</span>
              <span class="budget-amount numeric">
                ¥{{ Number(b.spent).toFixed(0) }}
                <span class="muted">/ ¥{{ Number(b.budget).toFixed(0) }}</span>
              </span>
            </div>
            <span
              class="budget-percent"
              :class="b.percent >= 100 ? 'over' : b.percent >= 80 ? 'warn' : 'normal'"
            >
              {{ b.percent.toFixed(0) }}%
            </span>
          </div>
          <BaseProgress
            :value="Math.min(b.percent, 100)"
            :variant="b.percent >= 100 ? 'danger' : b.percent >= 80 ? 'warning' : 'accent'"
            :show-label="false"
          />
          <div class="budget-actions">
            <BaseButton variant="ghost" size="sm" @click="openEdit(b)">修改</BaseButton>
            <BaseButton variant="danger" size="sm" @click="confirmDelete(b)">删除</BaseButton>
          </div>
        </BaseCard>
      </div>

      <!-- 添加预算按钮 -->
      <BaseButton
        v-if="!showAddForm"
        variant="primary"
        size="lg"
        block
        @click="openAdd"
        class="add-btn"
      >
        + 添加预算
      </BaseButton>

      <!-- 添加/编辑预算表单 -->
      <BaseCard v-else padding="md" class="form-card">
        <BaseEyebrow tone="accent">
          {{ editTarget ? '修改预算' : '添加预算' }}
        </BaseEyebrow>
        <h3 class="form-title display">
          {{ editTarget ? editTarget.category : '设置分类预算' }}
        </h3>

        <!-- 分类选择（仅添加时显示） -->
        <div v-if="!editTarget" class="form-group">
          <label class="form-label">分类</label>
          <div v-if="categoriesLoading" class="cat-loading">
            <span class="loading-spinner"></span> 加载分类中...
          </div>
          <div v-else-if="availableCategories.length === 0" class="cat-empty">
            <p class="empty-text">没有可设置的支出分类</p>
            <p class="empty-hint">
              {{ userCategories.length === 0 ? '分类还在加载，请稍候' : '所有支出类都已设预算或没有支出分类' }}
            </p>
            <button class="reload-btn" @click="loadUserCategories">🔄 重新加载分类</button>
          </div>
          <div v-else class="cat-grid">
            <button
              v-for="c in availableCategories"
              :key="c"
              class="cat-chip"
              :class="{ active: form.category === c }"
              @click="form.category = c"
            >{{ c }}</button>
          </div>
        </div>

        <!-- 金额 -->
        <div class="form-group">
          <label class="form-label">预算金额 (¥)</label>
          <div class="amount-row">
            <span class="amount-sign">¥</span>
            <input
              v-model.number="form.amount"
              type="number"
              placeholder="0.00"
              class="amount-input"
              min="0"
              step="0.01"
            />
          </div>
        </div>

        <!-- 错误 -->
        <div v-if="formError" class="alert alert-error">{{ formError }}</div>

        <div class="form-actions">
          <BaseButton variant="ghost" @click="cancelForm">取消</BaseButton>
          <BaseButton
            variant="primary"
            :loading="submitting"
            :disabled="!isFormValid"
            @click="submitForm"
          >保存</BaseButton>
        </div>
      </BaseCard>
    </div>

    <!-- 删除确认弹窗 -->
    <BaseModal v-model="showDeleteConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">删除预算</p>
        <p class="confirm-msg">
          确定要删除「<b>{{ deleteTarget?.category }}</b>」的预算设置吗？
        </p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showDeleteConfirm = false">取消</BaseButton>
        <BaseButton variant="danger" @click="doDelete">删除</BaseButton>
      </template>
    </BaseModal>

    <!-- 底部留白 -->
    <div class="tabbar-safe"></div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { billAPI, categoryAPI } from '../api'
import {
  BaseButton, BaseCard, BaseEyebrow, BaseSectionHeader,
  BaseEmpty, BaseProgress, BaseModal,
} from '../components/base'
import IconBudget from '../components/IconBudget.vue'
import { t, useI18n, SUPPORTED_LANGUAGES } from '../i18n'

const { setLanguage, lang } = useI18n()

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const budgetList = ref([])
const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const showAddForm = ref(false)
const lastUpdatedAt = ref('')

// 当前是否在当月
const isCurrentMonth = computed(() => {
  const now = new Date()
  return year.value === now.getFullYear() && month.value === (now.getMonth() + 1)
})

function goCurrentMonth() {
  const now = new Date()
  year.value = now.getFullYear()
  month.value = now.getMonth() + 1
  loadBudgets()
}

// 强制刷新（绕开任何缓存）
async function forceRefresh() {
  budgetList.value = []
  await loadBudgets()
  await loadUserCategories()
}
const editTarget = ref(null)
const deleteTarget = ref(null)
const showDeleteConfirm = ref(false)
const formError = ref('')

const form = reactive({ category: '', amount: 0 })

// 从 API 拉用户分类（系统 + 自定义）
const userCategories = ref([])
const categoriesLoading = ref(false)
async function loadUserCategories() {
  categoriesLoading.value = true
  try {
    const res = await categoryAPI.list()
    userCategories.value = res.data.categories || []
  } catch (e) {
    userCategories.value = []
  } finally {
    categoriesLoading.value = false
  }
}

const availableCategories = computed(() => {
  const used = budgetList.value.map(b => b.category)
  // 只显示支出类 + 未被设预算的
  return userCategories.value
    .filter(c => c.type === 'expense' && !used.includes(c.name))
    .map(c => c.name)
})

const isFormValid = computed(() => {
  return form.category && form.amount > 0
})

async function loadBudgets() {
  loading.value = true
  try {
    const res = await billAPI.getBudget({
      year: year.value,
      month: month.value,
    })
    // 兼容后端返回结构：{ budget: [...], spent: {...}, percent: {...} } 或 [...]
    const data = res.data || {}
    if (Array.isArray(data)) {
      budgetList.value = data
    } else if (Array.isArray(data.budget)) {
      const list = data.budget.map(b => ({
        category: b.category,
        budget: b.amount,
        spent: (data.spent || {})[b.category] || 0,
        percent: (data.percent || {})[b.category] || 0,
      }))
      budgetList.value = list
    } else {
      budgetList.value = []
    }
    lastUpdatedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  } catch (err) {
    console.error('加载预算失败', err)
    budgetList.value = []
  } finally {
    loading.value = false
  }
}

function prevMonth() {
  if (month.value === 1) {
    month.value = 12
    year.value -= 1
  } else {
    month.value -= 1
  }
  loadBudgets()
}
function nextMonth() {
  if (month.value === 12) {
    month.value = 1
    year.value += 1
  } else {
    month.value += 1
  }
  loadBudgets()
}

function openAdd() {
  editTarget.value = null
  form.category = availableCategories.value[0] || ''
  form.amount = 0
  formError.value = ''
  showAddForm.value = true
}
function openEdit(b) {
  editTarget.value = b
  form.category = b.category
  form.amount = Number(b.budget)
  formError.value = ''
  showAddForm.value = true
}
function cancelForm() {
  showAddForm.value = false
  editTarget.value = null
  formError.value = ''
}
async function submitForm() {
  formError.value = ''
  submitting.value = true
  try {
    const monthStr = `${year.value}-${String(month.value).padStart(2, '0')}`
    await billAPI.setBudget({
      category: form.category,
      amount: form.amount,
      month: monthStr,
    })
    showAddForm.value = false
    editTarget.value = null
    await loadBudgets()
  } catch (err) {
    formError.value = err.message || '保存失败'
  } finally {
    submitting.value = false
  }
}
function confirmDelete(b) {
  deleteTarget.value = b
  showDeleteConfirm.value = true
}
async function doDelete() {
  if (!deleteTarget.value) return
  try {
    const monthStr = `${year.value}-${String(month.value).padStart(2, '0')}`
    await billAPI.deleteBudget({
      category: deleteTarget.value.category,
      month: monthStr,
    })
    showDeleteConfirm.value = false
    deleteTarget.value = null
    await loadBudgets()
  } catch (err) {
    console.error('删除预算失败', err)
    alert(err.message || '删除失败')
  }
}

onMounted(() => { loadUserCategories(); loadBudgets() })
</script>

<style scoped>
/* 用 flexbox 强制居中（避免 max-w-2xl + mx-auto 在内容不足时偏左） */
.page-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;  /* 水平居中 */
}
.page-content {
  width: 100%;
  max-width: 42rem;     /* 等同 Tailwind max-w-2xl */
  padding: 0 16px 96px;
  box-sizing: border-box;
}

.nav {
  position: sticky; top: 0; z-index: 10;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border-soft, #eee);
}
.nav-inner {
  width: 100%;
  max-width: 768px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px;
  box-sizing: border-box;
}
.nav-left { display: flex; align-items: center; gap: 10px; }
.nav-icon { display: flex; align-items: center; }
.nav-title { font-size: 18px; font-weight: 600; margin: 0; }
.nav-actions { display: flex; align-items: center; gap: 8px; }
.icon-btn {
  background: transparent; border: none; padding: 6px;
  border-radius: 8px; cursor: pointer; color: var(--color-text-secondary, #555);
  display: inline-flex; align-items: center;
}
.icon-btn:hover { background: var(--color-border-soft, #f0f0f0); color: var(--color-text-primary, #111); }
.lang-select-inline {
  font-size: 13px; padding: 4px 8px;
  border: 1px solid var(--color-border-soft, #eee);
  border-radius: 6px; background: white;
}

.month-row {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 8px; padding: 8px 0;
}
.month-tools { display: flex; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f0f0f0; }
.tool-btn { flex: 1; padding: 6px 10px; border-radius: 6px; border: 1px solid #eee; background: white; color: #555; font-size: 12px; cursor: pointer; transition: all 0.15s; }
.tool-btn:hover:not(:disabled) { border-color: #d94f1e; color: #d94f1e; }
.tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.last-update { font-size: 11px; color: #999; margin: 8px 0 0; text-align: right; }

.month-nav {
  width: 36px; height: 36px; border-radius: 50%;
  border: 1px solid var(--color-border-soft, #eee);
  background: white; font-size: 20px; color: var(--color-text-primary, #111);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.month-nav:hover { background: var(--color-border-soft, #f0f0f0); }
.month-label { font-size: 18px; font-weight: 600; }

.loading-state {
  text-align: center; padding: 48px 16px;
  color: var(--color-text-secondary, #666);
  display: flex; flex-direction: column; align-items: center; gap: 12px;
}
.loading-spinner {
  width: 24px; height: 24px;
  border: 2px solid var(--color-border-soft, #eee);
  border-top-color: var(--color-action-accent, #d94f1e);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.budget-cards { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.budget-card { display: flex; flex-direction: column; gap: 10px; }
.budget-head {
  display: flex; align-items: center; justify-content: space-between;
}
.budget-info { display: flex; flex-direction: column; gap: 2px; }
.budget-cat { font-size: 15px; font-weight: 600; }
.budget-amount { font-size: 13px; color: var(--color-text-primary, #111); }
.budget-amount .muted { color: var(--color-text-muted, #999); margin-left: 4px; }
.budget-percent {
  font-family: var(--font-num, monospace);
  font-size: 16px; font-weight: 600;
  padding: 2px 10px; border-radius: 999px;
}
.budget-percent.normal { color: var(--color-feedback-positive, #2e7d4f); background: #e8f5ed; }
.budget-percent.warn { color: #b8660e; background: #fff3e0; }
.budget-percent.over { color: white; background: #d94f1e; }
.budget-actions { display: flex; gap: 8px; justify-content: flex-end; }

.add-btn { margin-top: 16px; }

.form-card { display: flex; flex-direction: column; gap: 14px; }
.form-title { font-size: 16px; font-weight: 600; margin: 4px 0 0; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label {
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--color-text-secondary, #666);
}
.cat-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.cat-loading { display: flex; align-items: center; gap: 8px; padding: 12px 0; color: #888; font-size: 13px; }
.cat-loading .loading-spinner { width: 14px; height: 14px; border: 2px solid #eee; border-top-color: #d94f1e; border-radius: 50%; animation: spin 0.8s linear infinite; }
.cat-empty { padding: 16px; text-align: center; background: #fff5f0; border-radius: 8px; }
.cat-empty .empty-text { font-size: 14px; color: #b53d12; margin: 0 0 4px; }
.cat-empty .empty-hint { font-size: 12px; color: #999; margin: 0 0 12px; }
.cat-empty .reload-btn { background: #d94f1e; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.cat-empty .reload-btn:hover { background: #b53d12; }
.cat-chip {
  padding: 6px 14px; border-radius: 999px;
  border: 1px solid var(--color-border-soft, #eee);
  background: white; font-size: 13px;
  color: var(--color-text-secondary, #555);
  cursor: pointer; transition: all 0.15s;
}
.cat-chip:hover { border-color: var(--color-action-accent, #d94f1e); }
.cat-chip.active {
  background: var(--color-action-accent, #d94f1e);
  color: white; border-color: transparent;
}

.amount-row {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 14px; border: 1px solid var(--color-border-soft, #eee);
  border-radius: 8px; background: white;
}
.amount-row:focus-within { border-color: var(--color-action-accent, #d94f1e); }
.amount-sign { font-size: 18px; color: var(--color-text-muted, #999); }
.amount-input {
  flex: 1; border: none; outline: none; font-size: 18px;
  font-family: var(--font-num, monospace); background: transparent;
}

.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
.alert {
  padding: 10px 14px; border-radius: 8px; font-size: 13px;
}
.alert-error {
  background: #fff5f0; border: 1px solid #f5c5a8; color: #b53d12;
}

.confirm-content { text-align: center; padding: 8px 0; }
.confirm-title { font-size: 18px; font-weight: 600; margin: 0 0 12px; }
.confirm-msg { font-size: 14px; color: var(--color-text-secondary, #555); line-height: 1.6; }

.tabbar-safe { height: 64px; }
</style>
