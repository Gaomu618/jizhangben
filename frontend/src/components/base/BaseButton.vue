<template>
  <button
    :type="type"
    :class="['btn', `btn-${variant}`, `btn-${size}`, { 'btn-loading': loading, 'btn-block': block, 'btn-icon-only': iconOnly }]"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    @click="onClick"
  >
    <span v-if="loading" class="spinner" aria-hidden="true"></span>
    <slot v-else name="icon"></slot>
    <span v-if="!iconOnly" class="btn-label"><slot /></span>
  </button>
</template>

<script setup>
const emit = defineEmits(['click'])

defineProps({
  variant: { type: String, default: 'primary' },  // primary | accent | ghost | soft | dark
  size:    { type: String, default: 'md' },        // sm(32) | md(40) | lg(48) | xl(56)
  type:    { type: String, default: 'button' },
  loading: { type: Boolean, default: false },
  disabled:{ type: Boolean, default: false },
  block:   { type: Boolean, default: false },
  iconOnly:{ type: Boolean, default: false },
})

function onClick(e) {
  // loading / disabled 状态下不触发（与 :disabled 视觉一致）
  // 注意：emit 之前先检查（虽然 :disabled 应该已经阻止）
  emit('click', e)
}
</script>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid transparent;
  border-radius: var(--btn-radius);
  font-family: inherit;
  font-weight: 600;
  cursor: pointer;
  transition:
    background var(--t-fast) var(--ease-out),
    border-color var(--t-fast) var(--ease-out),
    color var(--t-fast) var(--ease-out),
    box-shadow var(--t-fast) var(--ease-out),
    transform var(--t-fast) var(--ease-out);
  white-space: nowrap;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
.btn:focus-visible {
  outline: 2px solid var(--color-action-accent);
  outline-offset: 2px;
}
.btn:disabled, .btn[aria-busy="true"] {
  cursor: not-allowed;
  opacity: 0.55;
}
.btn:active:not(:disabled) { transform: translateY(1px); }
.btn-block { width: 100%; }

/* ============== Sizes ============== */
.btn-sm { height: 32px; padding: 0 12px; font-size: 13px; }
.btn-md { height: 40px; padding: 0 16px; font-size: 14px; }
.btn-lg { height: 48px; padding: 0 20px; font-size: 15px; }
.btn-xl { height: 56px; padding: 0 28px; font-size: 16px; letter-spacing: 0.04em; }

/* ============== Variants ============== */
/* primary — 深色实心（默认 CTA） */
.btn-primary {
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  box-shadow: var(--btn-primary-shadow);
}
.btn-primary:hover:not(:disabled) { background: var(--ink-800); box-shadow: var(--shadow-md); }

/* accent — 橙色实心（强调 CTA） */
.btn-accent {
  background: var(--btn-accent-bg);
  color: var(--color-text-inverse);
  box-shadow: 0 4px 14px rgba(217, 79, 30, 0.25);
}
.btn-accent:hover:not(:disabled) { background: #b53d12; box-shadow: 0 6px 20px rgba(217, 79, 30, 0.32); }

/* ghost — 透明边框 */
.btn-ghost {
  background: transparent;
  color: var(--color-text-primary);
  border-color: var(--color-border);
}
.btn-ghost:hover:not(:disabled) { background: var(--paper-50); border-color: var(--muted-2); }

/* soft — 浅底描边 */
.btn-soft {
  background: var(--paper-200);
  color: var(--color-text-primary);
  border-color: transparent;
}
.btn-soft:hover:not(:disabled) { background: var(--orange-50); color: var(--color-action-accent); }

/* dark — 反色（深底上用） */
.btn-dark {
  background: var(--paper-50);
  color: var(--ink-900);
}
.btn-dark:hover:not(:disabled) { background: white; }

/* icon-only 圆角 */
.btn-icon-only {
  padding: 0;
  aspect-ratio: 1;
}
.btn-sm.btn-icon-only { width: 32px; }
.btn-md.btn-icon-only { width: 40px; }
.btn-lg.btn-icon-only { width: 48px; }
</style>
