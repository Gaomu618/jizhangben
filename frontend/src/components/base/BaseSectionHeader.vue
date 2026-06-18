<template>
  <header class="section-header" :class="{ 'has-aside': $slots.aside }">
    <div class="header-text">
      <BaseEyebrow v-if="eyebrow" :tone="eyebrowTone">{{ eyebrow }}</BaseEyebrow>
      <h2 v-if="title" class="section-title display">{{ title }}</h2>
      <p v-if="subtitle" class="section-subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.aside" class="header-aside">
      <slot name="aside" />
    </div>
  </header>
</template>

<script setup>
import BaseEyebrow from './BaseEyebrow.vue'

defineProps({
  eyebrow:     { type: String, default: '' },
  eyebrowTone: { type: String, default: 'accent' },
  title:       { type: String, default: '' },
  subtitle:    { type: String, default: '' },
})
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.header-text { display: flex; flex-direction: column; gap: 6px; }

.section-title {
  font-size: 24px;
  font-weight: 500;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
  margin: 0;
}
.section-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  max-width: 560px;
}
.header-aside { display: flex; gap: 8px; align-items: center; }
</style>
