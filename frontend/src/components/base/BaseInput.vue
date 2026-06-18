<template>
  <div :class="['base-input', `size-${size}`, `variant-${variant}`, { 'has-error': error, 'is-disabled': disabled, 'is-readonly': readonly }]">
    <label v-if="label" :for="inputId" class="input-label">{{ label }}</label>

    <div class="input-wrap">
      <span v-if="$slots.prefix" class="input-affix prefix"><slot name="prefix" /></span>

      <input
        v-if="!multiline"
        :id="inputId"
        :type="resolvedType"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :autocomplete="autocomplete"
        :inputmode="inputmode"
        :aria-invalid="error || undefined"
        :aria-describedby="error ? `${inputId}-error` : (hint ? `${inputId}-hint` : undefined)"
        @input="onInput"
        @blur="$emit('blur', $event)"
        @focus="$emit('focus', $event)"
      />

      <textarea
        v-else
        :id="inputId"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :rows="rows"
        :aria-invalid="error || undefined"
        @input="onInput"
      />

      <span v-if="$slots.suffix || type === 'password'" class="input-affix suffix">
        <slot name="suffix" />
        <button
          v-if="type === 'password' && showTogglePassword"
          type="button"
          class="toggle-eye"
          :aria-label="isPasswordShown ? '隐藏密码' : '显示密码'"
          @click="isPasswordShown = !isPasswordShown"
        >
          <svg v-if="isPasswordShown" width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M3 3l18 18" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <path d="M10.5 6.5a4 4 0 0 0 5.7 5.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            <path d="M9.9 5.1A10 10 0 0 1 12 5c5 0 9 4 10 7-0.3 1-1 2-2 3M6.6 6.6C4 8.3 2.4 10.7 2 12c1 3 5 7 10 7 1.5 0 3-0.4 4.3-1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6"/>
          </svg>
        </button>
      </span>
    </div>

    <p v-if="error" :id="`${inputId}-error`" class="input-message error">{{ error }}</p>
    <p v-else-if="hint" :id="`${inputId}-hint`" class="input-message hint">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed, ref, useId } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label:      { type: String, default: '' },
  type:       { type: String, default: 'text' },
  variant:    { type: String, default: 'default' },   // default | filled | flushed | readonly
  size:       { type: String, default: 'md' },          // sm | md | lg
  placeholder:{ type: String, default: '' },
  hint:       { type: String, default: '' },
  error:      { type: String, default: '' },
  disabled:   { type: Boolean, default: false },
  readonly:   { type: Boolean, default: false },
  multiline:  { type: Boolean, default: false },
  rows:       { type: Number, default: 3 },
  autocomplete: { type: String, default: undefined },
  inputmode:  { type: String, default: undefined },
  showTogglePassword: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus'])

const inputId = useId()
const isPasswordShown = ref(false)

const resolvedType = computed(() => {
  if (props.type === 'password' && isPasswordShown.value) return 'text'
  return props.type
})

function onInput(e) {
  emit('update:modelValue', e.target.value)
}
</script>

<style scoped>
.base-input { display: flex; flex-direction: column; gap: 6px; }

.input-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

.input-wrap {
  display: flex;
  align-items: center;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--input-radius);
  transition:
    border-color var(--t-fast) var(--ease-out),
    box-shadow var(--t-fast) var(--ease-out),
    background var(--t-fast) var(--ease-out);
}
.input-wrap:focus-within {
  border-color: var(--color-action-accent);
  box-shadow: 0 0 0 3px rgba(217, 79, 30, 0.12);
  background: white;
}

.input-affix {
  display: inline-flex;
  align-items: center;
  color: var(--color-text-muted);
  padding: 0 12px;
}
.input-affix.prefix { padding-right: 0; }
.input-affix.suffix { padding-left: 0; }

input, textarea {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--color-text-primary);
  font-family: inherit;
  width: 100%;
}
input::placeholder, textarea::placeholder { color: var(--color-text-muted); }

.size-sm input, .size-sm textarea { padding: 8px 12px; font-size: 13px; }
.size-md input, .size-md textarea { padding: 12px 14px; font-size: 14.5px; }
.size-lg input, .size-lg textarea { padding: 14px 16px; font-size: 16px; }

.variant-filled .input-wrap { background: var(--paper-200); }
.variant-flushed {
  border-radius: 0;
}
.variant-flushed .input-wrap {
  border: none;
  border-bottom: 1px solid var(--color-border);
  border-radius: 0;
  background: transparent;
  padding: 0;
}
.variant-flushed .input-wrap:focus-within { border-bottom-color: var(--color-action-accent); box-shadow: none; }

.is-readonly .input-wrap { background: var(--paper-200); }
.is-disabled .input-wrap { background: var(--paper-200); opacity: 0.6; cursor: not-allowed; }

.has-error .input-wrap { border-color: var(--color-feedback-negative); }
.has-error .input-wrap:focus-within { box-shadow: 0 0 0 3px rgba(217, 79, 30, 0.18); }

.toggle-eye {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 6px;
  display: inline-flex;
  border-radius: 6px;
  transition: color var(--t-fast) var(--ease-out);
}
.toggle-eye:hover { color: var(--color-text-primary); }

.input-message { font-size: 11px; line-height: 1.4; min-height: 14px; }
.input-message.hint  { color: var(--color-text-muted); }
.input-message.error { color: var(--color-feedback-negative); }
</style>
