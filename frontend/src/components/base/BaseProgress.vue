<template>
  <div :class="['base-progress', `variant-${variant}`, { 'is-over': isOver }]">
    <div v-if="showLabel" class="progress-label-row">
      <span class="label-text"><slot name="label">{{ label }}</slot></span>
      <span class="label-value numeric">{{ Math.min(percent, 999) }}%</span>
    </div>
    <div class="progress-track" :aria-valuenow="Math.round(percent)" :aria-valuemin="0" :aria-valuemax="100" role="progressbar">
      <div class="progress-fill" :style="{ width: clampedWidth + '%' }"></div>
    </div>
    <p v-if="$slots.caption || caption" class="progress-caption"><slot name="caption">{{ caption }}</slot></p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value:     { type: Number, required: true },         // 0-100
  max:       { type: Number, default: 100 },
  variant:   { type: String, default: 'auto' },        // auto | accent | positive | warning
  label:     { type: String, default: '' },
  caption:   { type: String, default: '' },
  showLabel: { type: Boolean, default: true },
})

const percent = computed(() => (props.value / props.max) * 100)
const clampedWidth = computed(() => Math.min(Math.max(props.value, 0), 100))
const isOver = computed(() => percent.value >= 100)
</script>

<style scoped>
.base-progress { display: flex; flex-direction: column; gap: 6px; }

.progress-label-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  font-size: 12px;
}
.label-text { color: var(--color-text-secondary); font-weight: 500; }
.label-value { color: var(--color-text-primary); font-weight: 600; font-size: 13px; }

.progress-track {
  width: 100%;
  height: 6px;
  background: var(--paper-200);
  border-radius: 999px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: var(--color-text-primary);
  border-radius: 999px;
  transition: width var(--t-slow) var(--ease-out), background var(--t-fast) var(--ease-out);
}

.variant-accent .progress-fill { background: var(--color-action-accent); }
.variant-positive .progress-fill { background: var(--color-feedback-positive); }
.variant-warning .progress-fill { background: var(--color-feedback-warning); }

.is-over .progress-fill { background: var(--color-feedback-negative); }

.progress-caption {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 2px;
}
</style>
