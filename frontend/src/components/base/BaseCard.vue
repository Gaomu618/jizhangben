<template>
  <component
    :is="as"
    :class="['base-card', `card-${variant}`, `card-pad-${padding}`, { 'is-hoverable': hoverable, 'is-selected': selected, 'is-disabled': disabled }]"
    :tabindex="hoverable || selected ? 0 : undefined"
    :aria-disabled="disabled || undefined"
  >
    <slot />
  </component>
</template>

<script setup>
defineProps({
  as:        { type: String, default: 'div' },
  variant:   { type: String, default: 'default' },  // default | dark | bordered | gradient
  padding:   { type: String, default: 'md' },        // sm(16) | md(24) | lg(32)
  hoverable: { type: Boolean, default: false },
  selected:  { type: Boolean, default: false },
  disabled:  { type: Boolean, default: false },
})
</script>

<style scoped>
.base-card {
  position: relative;
  border-radius: var(--card-radius);
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  transition:
    border-color var(--t-fast) var(--ease-out),
    box-shadow var(--t-base) var(--ease-out),
    transform var(--t-base) var(--ease-out);
}
.base-card:focus-visible { outline: 2px solid var(--color-action-accent); outline-offset: 2px; }

/* ============== Variants ============== */
.card-default {}
.card-bordered { border-color: var(--color-border); }
.card-dark {
  background: var(--color-bg-deep);
  color: var(--color-text-inverse);
  border: none;
  box-shadow: var(--shadow-lg);
}
.card-gradient {
  background: linear-gradient(135deg, var(--paper-50) 0%, var(--card-bg) 50%, var(--orange-50) 100%);
  border-color: var(--color-border-soft);
}

/* ============== Padding ============== */
.card-pad-sm { padding: 16px; }
.card-pad-md { padding: 24px; }
.card-pad-lg { padding: 32px; }

/* ============== States ============== */
.is-hoverable { cursor: pointer; }
.is-hoverable:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--muted-2);
}
.is-selected {
  border-color: var(--color-action-accent);
  box-shadow: 0 0 0 3px rgba(217, 79, 30, 0.12);
}
.is-disabled { opacity: 0.5; cursor: not-allowed; }

/* Dark 卡片里的文字要反转色 */
.card-dark :deep(.text-muted),
.card-dark :deep(.text-secondary) { color: rgba(253, 251, 246, 0.55); }
.card-dark :deep(.eyebrow) { color: rgba(253, 251, 246, 0.55); }
</style>
