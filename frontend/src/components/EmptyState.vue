<template>
  <BaseEmpty :title="title" :message="message">
    <template v-if="icon" #icon>
      <component :is="icon" />
    </template>
    <template #cta>
      <slot />
    </template>
  </BaseEmpty>
</template>

<script setup>
import { BaseEmpty } from './base'

defineProps({
  title: { type: String, default: '暂无数据' },
  message: { type: String, default: '' },
  icon: { type: Object, default: null },
})
</script>
