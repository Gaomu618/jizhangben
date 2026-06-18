<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" :aria-label="name" role="img">
    <path d="M8 4.5a3 3 0 0 0-3 3v1a3 3 0 0 0-1 5.7V16a3 3 0 0 0 4 2.8V8.5a3 3 0 0 0-1-2.3 3 3 0 0 1 1-1.7Z"
          stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M16 4.5a3 3 0 0 1 3 3v1a3 3 0 0 1 1 5.7V16a3 3 0 0 1-4 2.8V8.5a3 3 0 0 1 1-2.3 3 3 0 0 0-1-1.7Z"
          stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M12 7v10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" opacity="0.5"/>
  </svg>
</template>

<script setup>
defineProps({
  size: { type: [Number, String], default: 20 },
  name: { type: String, default: '分类记忆' },
})
</script>
