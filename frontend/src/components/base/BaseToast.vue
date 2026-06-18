<template>
  <Teleport to="body">
    <Transition name="toast">
      <div
        v-if="modelValue"
        :class="['base-toast', `toast-${tone}`, `toast-pos-${position}`]"
        role="status"
        :aria-live="tone === 'error' ? 'assertive' : 'polite'"
      >
        <span class="toast-icon" aria-hidden="true">
          <svg v-if="tone === 'success'" width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M5 12l5 5L20 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else-if="tone === 'error'" width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.8"/>
            <path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.8"/>
            <path d="M12 16v-4M12 8h.01" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </span>
        <span class="toast-msg">{{ message }}</span>
        <button v-if="dismissible" class="toast-close" @click="dismiss" aria-label="关闭">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue:  { type: Boolean, required: true },
  message:     { type: String, required: true },
  tone:        { type: String, default: 'info' },      // info | success | error
  position:    { type: String, default: 'top' },       // top | bottom
  duration:    { type: Number, default: 3000 },
  dismissible: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'close'])

function dismiss() {
  emit('update:modelValue', false)
  emit('close')
}
</script>

<style scoped>
.base-toast {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--card-bg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  font-size: 13.5px;
  font-weight: 500;
  font-family: var(--font-body);
  z-index: 1100;
  min-width: 200px;
  max-width: 80vw;
  backdrop-filter: blur(12px);
}
.toast-pos-top    { top: 24px; }
.toast-pos-bottom { bottom: 24px; }

.toast-info    { color: var(--color-text-primary); border-color: var(--color-border); }
.toast-success { color: var(--color-feedback-positive); border-color: rgba(4, 120, 87, 0.3); background: var(--green-50); }
.toast-error   { color: var(--color-feedback-negative); border-color: rgba(181, 61, 18, 0.3); background: var(--orange-50); }

.toast-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.toast-msg { flex: 1; }

.toast-close {
  background: transparent;
  border: none;
  padding: 4px;
  margin: -4px -4px -4px 0;
  cursor: pointer;
  color: inherit;
  opacity: 0.6;
  display: inline-flex;
  border-radius: 6px;
  transition: opacity var(--t-fast) var(--ease-out);
}
.toast-close:hover { opacity: 1; }

/* Transitions */
.toast-enter-active, .toast-leave-active {
  transition: opacity var(--t-base) var(--ease-out), transform var(--t-base) var(--ease-out);
}
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}
.toast-pos-bottom.toast-enter-from,
.toast-pos-bottom.toast-leave-to {
  transform: translateX(-50%) translateY(8px);
}
</style>
