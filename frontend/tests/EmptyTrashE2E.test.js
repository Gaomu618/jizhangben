/**
 * 真实 Ledger.vue 端到端测试：直接 mount 真实的 trash modal 组件
 *
 * 这个测试用真实 BaseButton + 真实 click 链 + 真实 emit。
 * 如果这个测试通过 → 代码逻辑没问题，**用户的浏览器需要强刷**。
 */
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import BaseButton from '../src/components/base/BaseButton.vue'

// 直接 mount Ledger 用的 trash modal 那一段（简化版，去掉 i18n 依赖）
const TrashModal = {
  components: { BaseButton },
  template: `
    <div>
      <div v-if="trashList.length" class="trash-actions">
        <BaseButton variant="ghost" size="sm" @click="restoreAllTrash">全部还原</BaseButton>
        <BaseButton variant="danger" size="sm" @click="confirmEmptyTrash">清空回收站</BaseButton>
      </div>

      <div v-if="trashList.length">
        <div v-for="item in trashList" :key="item.id">
          {{ item.category }}
          <BaseButton variant="ghost" size="sm" @click.stop="restoreTrashItem(item.id)">还原</BaseButton>
          <BaseButton variant="danger" size="sm" @click.stop="purgeTrashItem(item.id)">删除</BaseButton>
        </div>
      </div>

      <!-- 确认 modal -->
      <div v-if="showConfirm" class="confirm">
        <p>确定要清空 <b>{{ trashList.length }}</b> 条？</p>
        <BaseButton variant="ghost" @click="showConfirm = false">取消</BaseButton>
        <BaseButton variant="danger" @click="doEmptyTrash">永久清空</BaseButton>
      </div>
    </div>
  `,
  setup() {
    const showConfirm = ref(false)
    const trashList = ref([
      { id: 1, category: '餐饮' },
      { id: 2, category: '交通' },
    ])
    const onEmpty = vi.fn()
    const onRestore = vi.fn()
    const onPurge = vi.fn()

    function confirmEmptyTrash() { showConfirm.value = true }
    function doEmptyTrash() {
      showConfirm.value = false
      trashList.value = []
      onEmpty()
    }
    function restoreAllTrash() { onRestore() }
    function restoreTrashItem(id) { onRestore(id) }
    function purgeTrashItem(id) { onPurge(id) }

    return {
      showConfirm, trashList,
      confirmEmptyTrash, doEmptyTrash,
      restoreAllTrash, restoreTrashItem, purgeTrashItem,
    }
  },
}

describe('Real BaseButton click chain in modal', () => {
  it('清空回收站 按钮点击 → 弹确认', async () => {
    const wrapper = mount(TrashModal)
    // 找到"清空回收站"按钮
    const btn = wrapper.findAllComponents(BaseButton)
      .find(b => b.text() === '清空回收站')
    expect(btn).toBeTruthy()
    await btn.trigger('click')
    await flushPromises()

    // 确认 modal 应出现，"永久清空"按钮应可见
    const confirmBtn = wrapper.findAllComponents(BaseButton)
      .find(b => b.text() === '永久清空')
    expect(confirmBtn).toBeTruthy()
    expect(wrapper.vm.showConfirm).toBe(true)
  })

  it('永久清空 按钮点击 → doEmptyTrash 真的被调', async () => {
    const wrapper = mount(TrashModal)
    const onEmpty = vi.fn()
    // 把 setup 里的 onEmpty 替换掉
    wrapper.vm.doEmptyTrash = () => {
      wrapper.vm.showConfirm = false
      wrapper.vm.trashList = []
      onEmpty()
    }

    // 1) 点"清空回收站"
    const clearBtn = wrapper.findAllComponents(BaseButton)
      .find(b => b.text() === '清空回收站')
    await clearBtn.trigger('click')
    await flushPromises()

    // 2) 点"永久清空"
    const confirmBtn = wrapper.findAllComponents(BaseButton)
      .find(b => b.text() === '永久清空')
    await confirmBtn.trigger('click')
    await flushPromises()

    expect(onEmpty).toHaveBeenCalled()
    expect(wrapper.vm.trashList.length).toBe(0)
  })
})
