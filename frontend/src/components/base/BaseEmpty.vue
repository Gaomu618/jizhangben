<template>
  <div class="base-empty">
    <div class="empty-icon">
      <slot name="icon">
        <svg width="56" height="56" viewBox="0 0 64 64" fill="none" aria-hidden="true">
          <circle cx="32" cy="32" r="30" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 4" opacity="0.3"/>
          <path d="M22 32h20M32 22v20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/>
        </svg>
      </slot>
    </div>
    <h3 v-if="title" class="empty-title display">{{ title }}</h3>
    <p v-if="message" class="empty-message">{{ message }}</p>
    <div v-if="$slots.cta" class="empty-cta">
      <slot name="cta" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title:   { type: String, default: '' },
  message: { type: String, default: '' },
})
</script>

<style scoped>
.base-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 24px;
  color: var(--color-text-muted);
}

.empty-icon {
  color: var(--muted-2);
  margin-bottom: 16px;
  opacity: 0.7;
}

.empty-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.empty-message {
  font-size: 14px;
  color: var(--color-text-secondary);
  max-width: 360px;
  line-height: 1.6;
  margin-bottom: 16px;
}

.empty-cta { margin-top: 8px; }
</style>
