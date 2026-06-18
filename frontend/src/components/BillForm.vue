<template>
  <BaseModal :model-value="true" title="添加账单" size="md" @update:model-value="$emit('close')" @close="$emit('close')">
    <form @submit.prevent="handleSubmit" class="bill-form">
      <BaseInput v-model="form.date" type="date" label="日期" required />
      <BaseInput v-model.number="form.amount" type="number" label="金额" placeholder="0.00" step="0.01" min="0" required />

      <BaseSelect v-model="form.type" label="类型" :options="typeOptions" />

      <BaseInput
        v-model="form.category"
        label="分类"
        placeholder="如：餐饮、工资、购物"
        list="categories"
        required
      />
      <datalist id="categories">
        <option value="餐饮" />
        <option value="交通" />
        <option value="购物" />
        <option value="娱乐" />
        <option value="工资" />
        <option value="奖金" />
        <option value="投资收益" />
        <option value="其他收入" />
      </datalist>

      <BaseInput v-model="form.note" label="备注" placeholder="可选" :multiline="true" :rows="2" />
    </form>

    <template #footer>
      <BaseButton variant="ghost" @click="$emit('close')">取消</BaseButton>
      <BaseButton variant="primary" @click="handleSubmit">添加</BaseButton>
    </template>
  </BaseModal>
</template>

<script setup>
import { reactive } from 'vue'
import { BaseModal, BaseInput, BaseSelect, BaseButton } from './base'

const emit = defineEmits(['close', 'save'])

const today = new Date().toISOString().split('T')[0]
const form = reactive({
  date: today,
  amount: '',
  type: 'expense',
  category: '',
  note: '',
})

const typeOptions = [
  { value: 'expense', label: '支出' },
  { value: 'income', label: '收入' },
]

function handleSubmit() {
  if (!form.date || !form.amount || !form.type || !form.category) {
    return
  }
  emit('save', { ...form })
}
</script>

<style scoped>
.bill-form { display: flex; flex-direction: column; gap: 14px; }
</style>
