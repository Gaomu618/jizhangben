<template>
  <label :class="['base-toggle', `size-${size}`, { 'is-checked': modelValue, 'is-disabled': disabled }]">
    <input
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <span class="toggle-track" aria-hidden="true">
      <span class="toggle-thumb"></span>
    </span>
    <span v-if="label || $slots.default" class="toggle-label">
      <slot>{{ label }}</slot>
    </span>
  </label>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  label:      { type: String, default: '' },
  size:       { type: String, default: 'md' },  // sm | md | lg
  disabled:   { type: Boolean, default: false },
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.base-toggle {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  font-size: 14px;
  color: var(--color-text-primary);
}
.base-toggle input { position: absolute; opacity: 0; pointer-events: none; }

.toggle-track {
  position: relative;
  display: inline-block;
  background: var(--paper-200);
  border-radius: 999px;
  transition: background var(--t-fast) var(--ease-out);
}
.toggle-thumb {
  position: absolute;
  top: 50%;
  left: 3px;
  transform: translateY(-50%);
  background: white;
  border-radius: 50%;
  box-shadow: var(--shadow-sm);
  transition: left var(--t-fast) var(--ease-out);
}

.size-sm .toggle-track { width: 28px; height: 16px; }
.size-sm .toggle-thumb { width: 12px; height: 12px; }
.size-md .toggle-track { width: 36px; height: 20px; }
.size-md .toggle-thumb { width: 16px; height: 16px; }
.size-lg .toggle-track { width: 44px; height: 24px; }
.size-lg .toggle-thumb { width: 20px; height: 20px; }

.is-checked .toggle-track { background: var(--color-action-accent); }
.is-checked.size-sm .toggle-thumb { left: 13px; }
.is-checked.size-md .toggle-thumb { left: 17px; }
.is-checked.size-lg .toggle-thumb { left: 21px; }

.is-disabled { opacity: 0.5; cursor: not-allowed; }

.toggle-label { font-size: 14px; color: var(--color-text-primary); }
</style>
