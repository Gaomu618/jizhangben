"""
前端组件契约测试：确保关键组件不丢失关键 API。

具体守护：BaseButton 必须 emit 'click' 事件。

历史教训：之前重构时 BaseButton 漏了 emit('click')，导致 30+ 个
@click 监听器全部静默失效（用户能点按钮但什么也不发生）。
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
BASE_BUTTON = ROOT / 'frontend' / 'src' / 'components' / 'base' / 'BaseButton.vue'


class TestBaseButtonContract:
    def test_emits_click_event(self):
        """BaseButton 必须显式 emit('click', e)，否则外部 @click 全失效"""
        content = BASE_BUTTON.read_text(encoding='utf-8')
        assert "defineEmits(['click'])" in content, (
            "BaseButton.vue 缺少 defineEmits(['click'])，"
            "会导致所有 <BaseButton @click=\"...\"> 静默失效"
        )

    def test_has_click_handler(self):
        """template 里必须有 @click 转发到 emit 的处理函数"""
        content = BASE_BUTTON.read_text(encoding='utf-8')
        # 必须有 @click="onClick" 或类似显式转发
        assert '@click=' in content and 'emit(' in content, (
            "BaseButton 内部 <button> 必须显式 @click 转发到 emit"
        )


class TestAllBaseComponentsCompile:
    """确保 base/ 目录下所有 .vue 文件都能被 Vite 编译（无语法错误）"""
    BASE_DIR = ROOT / 'frontend' / 'src' / 'components' / 'base'

    def test_all_vue_files_exist(self):
        expected = [
            'BaseButton.vue', 'BaseCard.vue', 'BaseInput.vue',
            'BaseSelect.vue', 'BaseTag.vue', 'BaseModal.vue',
            'BaseProgress.vue', 'BaseSparkline.vue', 'BaseEyebrow.vue',
            'BaseEmpty.vue', 'BaseSectionHeader.vue', 'BaseToggle.vue',
            'BaseAvatar.vue',
        ]
        for f in expected:
            assert (self.BASE_DIR / f).exists(), f"缺失基础组件: {f}"

    def test_all_have_template(self):
        for f in self.BASE_DIR.glob('*.vue'):
            content = f.read_text(encoding='utf-8')
            assert '<template>' in content, f"{f.name} 缺少 <template>"

    def test_all_have_script_setup(self):
        for f in self.BASE_DIR.glob('*.vue'):
            content = f.read_text(encoding='utf-8')
            assert '<script setup>' in content, f"{f.name} 缺少 <script setup>"


class TestTokensLayered:
    """确保 design tokens 三层架构保持完整"""
    TOKENS = ROOT / 'frontend' / 'src' / 'tokens.css'

    def test_primitive_layer_exists(self):
        content = self.TOKENS.read_text(encoding='utf-8')
        # Layer 1: Primitive
        assert '--ink-900' in content
        assert '--paper-100' in content
        assert '--orange-500' in content

    def test_semantic_layer_exists(self):
        content = self.TOKENS.read_text(encoding='utf-8')
        # Layer 2: Semantic
        assert '--color-bg-default' in content
        assert '--color-action-primary' in content
        assert '--color-feedback-positive' in content

    def test_component_layer_exists(self):
        content = self.TOKENS.read_text(encoding='utf-8')
        # Layer 3: Component
        assert '--btn-primary-bg' in content
        assert '--card-bg' in content
        assert '--input-radius' in content
