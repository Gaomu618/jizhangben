<template>
  <p :class="['eyebrow', `eyebrow-${tone}`]">
    <slot />
  </p>
</template>

<script setup>
defineProps({
  tone: { type: String, default: 'default' },  // default | accent | ink
})
</script>
