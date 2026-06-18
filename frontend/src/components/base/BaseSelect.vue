<template>
  <div :class="['base-select', `size-${size}`, { 'is-disabled': disabled }]">
    <label v-if="label" :for="selectId" class="select-label">{{ label }}</label>
    <div class="select-wrap">
      <select
        :id="selectId"
        :value="modelValue"
        :disabled="disabled"
        @change="onChange"
      >
        <option v-if="placeholder" value="" disabled hidden>{{ placeholder }}</option>
        <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <svg class="select-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { useId } from 'vue'

const props = defineProps({
  modelValue:  { type: [String, Number], default: '' },
  options:     { type: Array, default: () => [] },  // [{value, label}]
  label:       { type: String, default: '' },
  size:        { type: String, default: 'md' },      // sm | md | lg
  placeholder: { type: String, default: '' },
  disabled:    { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
const selectId = useId()

function onChange(e) {
  emit('update:modelValue', e.target.value)
}
</script>

<style scoped>
.base-select { display: flex; flex-direction: column; gap: 6px; }

.select-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

.select-wrap {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--input-radius);
  transition:
    border-color var(--t-fast) var(--ease-out),
    box-shadow var(--t-fast) var(--ease-out);
}
.select-wrap:focus-within {
  border-color: var(--color-action-accent);
  box-shadow: 0 0 0 3px rgba(217, 79, 30, 0.12);
}

select {
  flex: 1;
  appearance: none;
  -webkit-appearance: none;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text-primary);
  font-family: inherit;
  cursor: pointer;
  width: 100%;
}
.size-sm select { padding: 8px 32px 8px 12px; font-size: 13px; }
.size-md select { padding: 12px 36px 12px 14px; font-size: 14.5px; }
.size-lg select { padding: 14px 40px 14px 16px; font-size: 16px; }

.select-chevron {
  position: absolute;
  right: 12px;
  pointer-events: none;
  color: var(--color-text-muted);
}

.is-disabled .select-wrap { opacity: 0.55; cursor: not-allowed; }
.is-disabled select { cursor: not-allowed; }
</style>
