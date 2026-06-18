/**
 * BaseButton 契约测试：确保 @click 能正确触发
 *
 * 历史教训：之前 BaseButton 漏了 emit('click')，导致 30+ 个
 * @click 监听器全部静默失效（用户能点按钮但什么也不发生）。
 *
 * 此测试用真实 DOM（jsdom）+ 真实点击事件验证修复 work。
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseButton from '../src/components/base/BaseButton.vue'

describe('BaseButton', () => {
  it('emits click event when clicked', async () => {
    const wrapper = mount(BaseButton, { slots: { default: '清空回收站' } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('emits click with original MouseEvent', async () => {
    const wrapper = mount(BaseButton, { slots: { default: 'X' } })
    await wrapper.trigger('click')
    const events = wrapper.emitted('click')
    expect(events[0][0]).toBeInstanceOf(MouseEvent)
  })

  it('does NOT emit when disabled', async () => {
    const wrapper = mount(BaseButton, {
      props: { disabled: true },
      slots: { default: 'X' },
    })
    await wrapper.trigger('click')
    // 原生 button 在 disabled 状态下不会派发 click 事件（DOM 行为）
    // 所以这里检查 Vue 是否收到 emit
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('renders slot content', () => {
    const wrapper = mount(BaseButton, { slots: { default: '保存' } })
    expect(wrapper.text()).toBe('保存')
  })

  it('renders spinner when loading', () => {
    const wrapper = mount(BaseButton, {
      props: { loading: true },
      slots: { default: 'X' },
    })
    expect(wrapper.find('.spinner').exists()).toBe(true)
  })

  it('applies variant and size classes', () => {
    const wrapper = mount(BaseButton, {
      props: { variant: 'danger', size: 'lg' },
      slots: { default: 'X' },
    })
    expect(wrapper.classes()).toContain('btn-danger')
    expect(wrapper.classes()).toContain('btn-lg')
  })
})
