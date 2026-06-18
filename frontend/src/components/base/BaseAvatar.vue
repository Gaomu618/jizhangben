<template>
  <span :class="['base-avatar', `shape-${shape}`, `size-${size}`, { 'with-status': status }]">
    <span v-if="initials" class="avatar-initials">{{ initials }}</span>
    <span v-else-if="$slots.default" class="avatar-slot"><slot /></span>
    <span v-if="status" :class="['avatar-status', `status-${status}`]" aria-hidden="true"></span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name:   { type: String, default: '' },
  shape:  { type: String, default: 'circle' },   // circle | square | badge
  size:   { type: String, default: 'md' },       // sm(24) | md(40) | lg(84)
  status: { type: String, default: '' },         // online | away | busy | '' (none)
})

const initials = computed(() => {
  if (!props.name) return ''
  const trimmed = props.name.trim()
  if (!trimmed) return ''
  // 取第一个中文字符 或 前2个 ASCII
  if (/[一-龥]/.test(trimmed[0])) return trimmed[0]
  return trimmed.slice(0, 2).toUpperCase()
})
</script>

<style scoped>
.base-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--orange-500) 0%, var(--gold-500) 100%);
  color: white;
  font-weight: 600;
  font-family: var(--font-num);
  letter-spacing: 0.02em;
  flex-shrink: 0;
  user-select: none;
}

.shape-circle { border-radius: 50%; }
.shape-square { border-radius: 8px; }
.shape-badge  { border-radius: 6px; }

.size-sm { width: 24px; height: 24px; font-size: 10px; }
.size-md { width: 40px; height: 40px; font-size: 14px; }
.size-lg { width: 84px; height: 84px; font-size: 28px; }

.avatar-initials { line-height: 1; }

.with-status::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 30%;
  height: 30%;
  border-radius: 50%;
  border: 2px solid var(--card-bg);
}
.status-online::after { background: var(--color-feedback-positive); }
.status-away::after   { background: var(--color-feedback-warning); }
.status-busy::after   { background: var(--color-feedback-negative); }
</style>
