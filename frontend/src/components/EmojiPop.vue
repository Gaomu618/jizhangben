<template>
  <div
    class="fixed text-4xl pointer-events-none z-30"
    :style="{ bottom: '0px', left: x + 'px' }">
    <span ref="el" class="inline-block">{{ emoji }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  emoji: String,
  x: Number,
  delay: { type: Number, default: 0 }
})

const el = ref(null)

onMounted(() => {
  setTimeout(() => {
    if (el.value) {
      const halfH = window.innerHeight / 2
      el.value.closest('.fixed')?.style.setProperty('--half-screen', halfH + 'px')
      el.value.classList.add('emoji-boing')
      setTimeout(() => {
        el.value?.closest('.fixed')?.remove()
      }, 1000)
    }
  }, props.delay)
})
</script>

<style>
.emoji-boing {
  animation: boing 1.2s cubic-bezier(0.15, 0, 0.85, 0.35) forwards;
}
@keyframes boing {
  0%   { opacity: 0; transform: translateY(0) translateX(0) scale(0.3) rotate(0deg); }
  12%  { opacity: 1; transform: translateY(calc(var(--half-screen, 400px) * -1)) translateX(30px) scale(1.4) rotate(8deg); }
  35%  { opacity: 1; transform: translateY(calc(var(--half-screen, 400px) * -0.5)) translateX(-15px) scale(1.2) rotate(-5deg); }
  65%  { opacity: 1; transform: translateY(calc(var(--half-screen, 400px) * 0.1)) translateX(10px) scale(1) rotate(3deg); }
  100% { opacity: 0; transform: translateY(calc(var(--half-screen, 400px) * 1.2)) translateX(5px) scale(0.3) rotate(0deg); }
}
</style>