<template>
  <div class="min-h-screen app-bg page-wrap">
    <header class="nav">
      <div class="nav-inner">
        <div class="nav-left">
          <button class="icon-btn" @click="router.push('/')" title="返回">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <h1 class="nav-title display">分类管理</h1>
        </div>
      </div>
    </header>

    <div class="page-content">
      <!-- 顶部说明 -->
      <BaseCard padding="md" class="mb-4">
        <BaseEyebrow tone="accent">Custom · 自定义</BaseEyebrow>
        <p class="hint-text">
          系统分类 🔒 不可删；自定义分类最多 50 个，每个最多配 200 关键词。
        </p>
        <p class="hint-text" v-if="categories.length">
          当前 <b>{{ categories.length }}</b> 个（{{ systemCount }} 系统 / {{ customCount }} 自定义）
        </p>
      </BaseCard>

      <!-- 新增按钮 -->
      <BaseButton variant="primary" size="lg" block @click="openAdd" class="add-btn">
        + 新增自定义分类
      </BaseButton>

      <!-- 新增表单 -->
      <BaseCard v-if="showAddForm" padding="md" class="form-card">
        <BaseEyebrow tone="default">新增分类</BaseEyebrow>
        <div class="form-group">
          <label class="form-label">分类名</label>
          <BaseInput
            v-model="form.name"
            placeholder="如：宠物、健身、手办"
            :error="formError"
            maxlength="20"
            @input="onNameInput"
          />
        </div>
        <div class="form-group">
          <label class="form-label">图标（emoji，可选）</label>
          <div class="emoji-row">
            <button
              v-for="e in EMOJI_OPTIONS"
              :key="e"
              class="emoji-btn"
              :class="{ active: form.icon === e }"
              @click="form.icon = e"
            >{{ e }}</button>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">类型</label>
          <div class="type-row">
            <button
              class="type-pill"
              :class="{ active: form.type === 'expense' }"
              @click="form.type = 'expense'"
            >支出</button>
            <button
              class="type-pill"
              :class="{ active: form.type === 'income' }"
              @click="form.type = 'income'"
            >收入</button>
          </div>
        </div>
        <div v-if="formError" class="alert alert-error">{{ formError }}</div>
        <div class="form-actions">
          <BaseButton variant="ghost" @click="cancelForm">取消</BaseButton>
          <BaseButton variant="primary" :loading="submitting" :disabled="!isFormValid" @click="submitForm">保存</BaseButton>
        </div>
      </BaseCard>

      <!-- 分类列表 -->
      <BaseSectionHeader eyebrow="Categories · 分类" title="我的分类" />
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中…</span>
      </div>

      <div v-else class="cat-list">
        <BaseCard
          v-for="c in categories"
          :key="c.id"
          padding="md"
          class="cat-card"
          :class="{ 'is-expanded': expandedId === c.id }"
        >
          <div class="cat-head" @click="toggle(c.id)">
            <div class="cat-info">
              <span class="cat-icon">{{ c.icon || '📦' }}</span>
              <span class="cat-name display">{{ c.name }}</span>
              <span v-if="c.is_system" class="cat-badge">🔒 系统</span>
              <span v-else class="cat-badge cat-badge--custom">✏️ 自定义</span>
              <span class="cat-type">{{ c.type === 'income' ? '收入' : '支出' }}</span>
            </div>
            <div class="cat-actions">
              <BaseButton v-if="!c.is_system" variant="danger" size="sm" @click.stop="confirmDelete(c)">删除</BaseButton>
              <svg class="expand-icon" :class="{ rotated: expandedId === c.id }" width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>

          <!-- 展开：关键词管理 -->
          <div v-if="expandedId === c.id" class="cat-detail">
            <div class="kw-section">
              <BaseEyebrow tone="default">关键词（{{ keywords.length }}）</BaseEyebrow>
              <p class="kw-hint">智能分类时优先匹配这里的关键词（优先级高于系统字典）</p>
              <div v-if="keywords.length" class="kw-list">
                <span v-for="kw in keywords" :key="kw.id" class="kw-chip">
                  {{ kw.keyword }}
                  <button class="kw-del" @click="removeKw(kw.id)" title="删除">×</button>
                </span>
              </div>
              <p v-else class="kw-empty">还没有关键词，点击下方添加</p>
              <div class="kw-add-row">
                <input
                  v-model="newKw"
                  type="text"
                  placeholder="输入关键词回车添加"
                  class="kw-input"
                  maxlength="50"
                  @keyup.enter="addKw"
                />
                <BaseButton variant="primary" size="sm" @click="addKw" :disabled="!newKw.trim()">添加</BaseButton>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>

    <!-- 删除确认 -->
    <BaseModal v-model="showDelConfirm" size="sm" :show-close="false">
      <div class="confirm-content">
        <p class="confirm-title display">删除分类</p>
        <p class="confirm-msg">
          确定要删除「<b>{{ delTarget?.name }}</b>」分类吗？<br>
          <small class="muted">⚠️ 历史账单上的「{{ delTarget?.name }}」字符串会保留，但不再出现在分类选项中。</small>
        </p>
      </div>
      <template #footer>
        <BaseButton variant="ghost" @click="showDelConfirm = false">取消</BaseButton>
        <BaseButton variant="danger" @click="doDelete">删除</BaseButton>
      </template>
    </BaseModal>

    <div class="tabbar-safe"></div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { categoryAPI } from '../api'
import {
  BaseButton, BaseCard, BaseInput,
  BaseEyebrow, BaseSectionHeader, BaseModal,
} from '../components/base'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const categories = ref([])
const systemCount = ref(0)
const customCount = ref(0)

const showAddForm = ref(false)
const form = reactive({ name: '', icon: '', type: 'expense' })
const formError = ref('')

const expandedId = ref(null)
const keywords = ref([])
const newKw = ref('')

const showDelConfirm = ref(false)
const delTarget = ref(null)

const EMOJI_OPTIONS = ['🍔', '🚗', '🛒', '🎮', '🏠', '📚', '💊', '📦', '💰', '🎁', '📈', '💼', '🔄',
                       '🐶', '🐱', '🏋️', '🎨', '🎵', '✈️', '🌸', '☕', '🍕', '🎬', '💄', '⚽', '📷']

const isFormValid = computed(() => form.name.trim().length > 0 && form.name.trim().length <= 20)

async function loadCategories() {
  loading.value = true
  try {
    const res = await categoryAPI.list()
    categories.value = res.data.categories || []
    systemCount.value = res.data.system_count || 0
    customCount.value = res.data.custom_count || 0
  } catch (e) {
    console.error('加载分类失败', e)
  } finally {
    loading.value = false
  }
}

function openAdd() {
  form.name = ''
  form.icon = ''
  form.type = 'expense'
  formError.value = ''
  showAddForm.value = true
}

function cancelForm() {
  showAddForm.value = false
  formError.value = ''
}

function onNameInput() {
  formError.value = ''
}

async function submitForm() {
  if (!isFormValid.value) return
  submitting.value = true
  formError.value = ''
  try {
    await categoryAPI.create({
      name: form.name.trim(),
      icon: form.icon || null,
      type: form.type,
    })
    showAddForm.value = false
    await loadCategories()
  } catch (e) {
    formError.value = e.message || '保存失败'
  } finally {
    submitting.value = false
  }
}

async function toggle(catId) {
  if (expandedId.value === catId) {
    expandedId.value = null
    keywords.value = []
    newKw.value = ''
    return
  }
  expandedId.value = catId
  newKw.value = ''
  try {
    const res = await categoryAPI.listKeywords(catId)
    keywords.value = res.data.keywords || []
  } catch (e) {
    keywords.value = []
  }
}

async function addKw() {
  const kw = newKw.value.trim()
  if (!kw) return
  try {
    await categoryAPI.addKeyword(expandedId.value, { keyword: kw })
    newKw.value = ''
    // 刷新关键词
    const res = await categoryAPI.listKeywords(expandedId.value)
    keywords.value = res.data.keywords || []
  } catch (e) {
    alert(e.message || '添加失败')
  }
}

async function removeKw(kwId) {
  if (!confirm('删除这个关键词？')) return
  try {
    await categoryAPI.removeKeyword(kwId)
    keywords.value = keywords.value.filter(k => k.id !== kwId)
  } catch (e) {
    alert(e.message || '删除失败')
  }
}

function confirmDelete(c) {
  delTarget.value = c
  showDelConfirm.value = true
}

async function doDelete() {
  if (!delTarget.value) return
  try {
    await categoryAPI.remove(delTarget.value.id)
    showDelConfirm.value = false
    delTarget.value = null
    expandedId.value = null
    keywords.value = []
    await loadCategories()
  } catch (e) {
    alert(e.message || '删除失败')
  }
}

onMounted(loadCategories)
</script>

<style scoped>
.page-wrap { display: flex; flex-direction: column; align-items: center; }
.page-content { width: 100%; max-width: 42rem; padding: 0 16px 32px; box-sizing: border-box; }

.nav { position: sticky; top: 0; z-index: 10; background: rgba(255,255,255,0.85); backdrop-filter: blur(12px); border-bottom: 1px solid #eee; width: 100%; }
.nav-inner { width: 100%; max-width: 768px; margin: 0 auto; padding: 12px 16px; display: flex; align-items: center; gap: 10px; box-sizing: border-box; }
.nav-left { display: flex; align-items: center; gap: 10px; }
.nav-title { font-size: 18px; font-weight: 600; margin: 0; }
.icon-btn { background: transparent; border: none; padding: 6px; border-radius: 8px; cursor: pointer; color: #555; display: inline-flex; }
.icon-btn:hover { background: #f0f0f0; }

.hint-text { font-size: 13px; color: #666; margin: 8px 0 0; line-height: 1.6; }
.add-btn { margin: 16px 0; }

.form-card { display: flex; flex-direction: column; gap: 14px; margin-bottom: 20px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #666; }
.emoji-row { display: flex; flex-wrap: wrap; gap: 6px; }
.emoji-btn { width: 36px; height: 36px; border-radius: 8px; border: 1px solid #eee; background: white; font-size: 20px; cursor: pointer; }
.emoji-btn:hover { border-color: #d94f1e; }
.emoji-btn.active { background: #d94f1e; border-color: transparent; }
.type-row { display: flex; gap: 8px; }
.type-pill { padding: 8px 20px; border-radius: 999px; border: 1px solid #eee; background: white; font-size: 14px; color: #555; cursor: pointer; }
.type-pill.active { background: #d94f1e; color: white; border-color: transparent; }
.form-actions { display: flex; gap: 8px; justify-content: flex-end; }
.alert { padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.alert-error { background: #fff5f0; border: 1px solid #f5c5a8; color: #b53d12; }

.loading-state { text-align: center; padding: 48px 16px; color: #666; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.loading-spinner { width: 24px; height: 24px; border: 2px solid #eee; border-top-color: #d94f1e; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.cat-list { display: flex; flex-direction: column; gap: 10px; }
.cat-card { transition: all 0.2s; }
.cat-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; cursor: pointer; }
.cat-info { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.cat-icon { font-size: 22px; }
.cat-name { font-size: 15px; font-weight: 600; }
.cat-badge { font-size: 10px; padding: 2px 8px; border-radius: 999px; background: #f0f0f0; color: #888; white-space: nowrap; }
.cat-badge--custom { background: #fff5f0; color: #d94f1e; }
.cat-type { font-size: 12px; color: #999; }
.cat-actions { display: flex; align-items: center; gap: 6px; }
.expand-icon { transition: transform 0.2s; color: #999; }
.expand-icon.rotated { transform: rotate(180deg); }

.cat-detail { margin-top: 14px; padding-top: 14px; border-top: 1px solid #f0f0f0; }
.kw-section { display: flex; flex-direction: column; gap: 8px; }
.kw-hint { font-size: 12px; color: #888; margin: 4px 0; }
.kw-list { display: flex; flex-wrap: wrap; gap: 6px; }
.kw-chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #f5f5f5; border-radius: 999px; font-size: 13px; }
.kw-del { background: transparent; border: none; cursor: pointer; color: #999; font-size: 16px; padding: 0 4px; line-height: 1; }
.kw-del:hover { color: #d94f1e; }
.kw-empty { font-size: 12px; color: #aaa; padding: 8px 0; }
.kw-add-row { display: flex; gap: 6px; align-items: center; }
.kw-input { flex: 1; padding: 8px 12px; border: 1px solid #eee; border-radius: 6px; font-size: 13px; outline: none; font-family: inherit; }
.kw-input:focus { border-color: #d94f1e; }

.confirm-content { text-align: center; padding: 8px 0; }
.confirm-title { font-size: 18px; font-weight: 600; margin: 0 0 12px; }
.confirm-msg { font-size: 14px; color: #555; line-height: 1.6; }
.confirm-msg .muted { color: #999; font-size: 12px; }
.tabbar-safe { height: 32px; }
</style>
