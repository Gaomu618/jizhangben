<template>
  <BaseModal :model-value="true" title="编辑账单" size="md" @update:model-value="$emit('close')" @close="$emit('close')">
    <form @submit.prevent="handleSubmit" class="edit-form">
      <BaseInput v-model="form.date" type="date" label="日期" required />
      <BaseSelect v-model="form.type" label="类型" :options="typeOptions" />
      <BaseInput v-model="form.category" label="分类" placeholder="如：餐饮、工资、购物" required />
      <BaseInput v-model.number="form.amount" type="number" label="金额" placeholder="0.00" step="0.01" min="0" required />
      <BaseInput v-model="form.note" label="备注" placeholder="可选" :multiline="true" :rows="2" />
    </form>

    <template #footer>
      <BaseButton variant="ghost" @click="$emit('close')">取消</BaseButton>
      <BaseButton variant="primary" @click="handleSubmit">保存</BaseButton>
    </template>
  </BaseModal>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { BaseModal, BaseInput, BaseSelect, BaseButton } from './base'

const props = defineProps({
  record: { type: Object, required: true },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  date: '', type: 'expense', category: '', amount: 0, note: '',
})

const typeOptions = [
  { value: 'income', label: '收入' },
  { value: 'expense', label: '支出' },
]

watch(() => props.record, (newVal) => {
  if (newVal) {
    form.date = newVal.date || ''
    form.type = newVal.type || 'expense'
    form.category = newVal.category || ''
    form.amount = newVal.amount || 0
    form.note = newVal.note || ''
  }
}, { immediate: true })

function handleSubmit() {
  emit('save', { ...form })
}
</script>

<style scoped>
.edit-form { display: flex; flex-direction: column; gap: 14px; }
</style>
