<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-root" role="dialog" aria-modal="true" :aria-labelledby="titleId" @keydown.esc="close">
        <div class="modal-backdrop" @click="closeOnBackdrop && close()" aria-hidden="true"></div>
        <div :class="['modal-panel', `size-${size}`]">
          <header v-if="title || $slots.header" class="modal-header">
            <slot name="header">
              <h2 :id="titleId" class="modal-title">{{ title }}</h2>
            </slot>
            <button v-if="showClose" type="button" class="modal-close" aria-label="关闭" @click="close">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
              </svg>
            </button>
          </header>
          <div class="modal-body"><slot /></div>
          <footer v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, useSlots } from 'vue'

const props = defineProps({
  modelValue:      { type: Boolean, required: true },
  title:           { type: String, default: '' },
  size:            { type: String, default: 'md' },      // sm | md | lg
  showClose:       { type: Boolean, default: true },
  closeOnBackdrop: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'close'])

const slots = useSlots()
const titleId = computed(() => `modal-title-${Math.random().toString(36).slice(2, 8)}`)

function close() {
  emit('update:modelValue', false)
  emit('close')
}
</script>

<style scoped>
.modal-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
}

.modal-panel {
  position: relative;
  background: var(--card-bg);
  border-radius: var(--card-radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;
}

.size-sm { max-width: 380px; }
.size-md { max-width: 520px; }
.size-lg { max-width: 720px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-soft);
}
.modal-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
}
.modal-close {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  display: inline-flex;
  transition: background var(--t-fast) var(--ease-out), color var(--t-fast) var(--ease-out);
}
.modal-close:hover { background: var(--paper-200); color: var(--color-text-primary); }

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--color-border-soft);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

/* Transitions */
.modal-enter-active, .modal-leave-active {
  transition: opacity var(--t-base) var(--ease-out);
}
.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel {
  transition: transform var(--t-base) var(--ease-out), opacity var(--t-base) var(--ease-out);
}
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-panel { transform: translateY(8px) scale(0.98); opacity: 0; }
.modal-leave-to .modal-panel   { transform: translateY(4px) scale(0.99); opacity: 0; }
</style>
