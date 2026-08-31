# -*- coding: utf-8 -*-
"""RadioGroup：单选组控件（继承 Panel）。

- 内部使用 ``VBoxLayout`` / ``HBoxLayout`` 垂直或水平排列 ``_RadioButton``。
- ``_RadioButton`` 外观为圆形：未选中空心圆、选中实心圆（+ 内部白点），
  点击时向组报告自身索引。
- 构造参数：``rect`` / ``options`` / ``selected_index`` / ``on_select(index, text)`` / ``factory``。
- 点击选项：组遍历子项取消旧选中、选中当前，并调用 ``on_select``；
  外部程序可用 ``set_selected(index)`` 主动切换（不触发回调）。
"""

import sdl2
import sdl2.sdlgfx

from SDLCore.ui.panel import Panel
from SDLCore.ui.widget import Widget
from SDLCore.ui.label import Label
from SDLCore.ui.layout import VBoxLayout, HBoxLayout
from SDLCore.ui import apply_opacity


class _RadioButton(Widget):
    """单选圆点（RadioGroup 内部类）。"""

    RADIUS = 9
    BOX = 20
    GAP = 6
    COLOR_RING = (120, 120, 120, 255)       # 未选中圆环
    COLOR_CHECKED = (30, 120, 200, 255)     # 选中实心
    COLOR_CHECK_MARK = (255, 255, 255, 255) # 选中内部白点
    COLOR_TEXT = (30, 30, 30, 255)

    def __init__(self, group, index, text, factory, rect):
        super().__init__(rect)
        self.group = group
        self.index = index
        self.text = text
        self.checked = False
        # 圆点右侧文本
        self.label = Label(
            (self.BOX + self.GAP, 0, 0, self.BOX),
            text=text, color=self.COLOR_TEXT, font_size="14px", factory=factory,
        )

    def set_checked(self, checked: bool) -> None:
        self.checked = bool(checked)

    def measure(self, constraints=None):
        from SDLCore.ui.layout import Constraints
        if constraints is None:
            constraints = Constraints()
        tw = self.label.measure(constraints)[0] if self.text else 0
        w = self.BOX + self.GAP + tw
        h = max(self.BOX, self._hint_rect[3])
        return (constraints.clamp_w(w), constraints.clamp_h(h))

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if (
            event.type == sdl2.SDL_MOUSEBUTTONDOWN
            and event.button.button == sdl2.SDL_BUTTON_LEFT
            and self._contains(event.button.x, event.button.y)
        ):
            self.group.select(self.index)  # 向组报告自己的索引
            return True
        return False

    def render(self, renderer) -> None:
        if not self.visible:
            return
        x, y, w, h = self.abs_rect
        bx = x
        by = y + (h - self.BOX) // 2
        cx = bx + self.BOX // 2
        cy = by + self.BOX // 2
        r = self.RADIUS
        alpha = int(255 * self._render_opacity)
        if self.checked:
            # 实心圆（主题色）+ 内部白点
            sdl2.sdlgfx.filledCircleRGBA(
                renderer.sdlrenderer, cx, cy, r, *self.COLOR_CHECKED[:3], alpha
            )
            sdl2.sdlgfx.filledCircleRGBA(
                renderer.sdlrenderer, cx, cy, max(2, r - 5),
                *self.COLOR_CHECK_MARK[:3], alpha,
            )
        else:
            # 空心圆
            sdl2.sdlgfx.circleRGBA(
                renderer.sdlrenderer, cx, cy, r, *self.COLOR_RING[:3], alpha
            )
        # 文本（透明度传播）
        lx = x + self.BOX + self.GAP
        ly = y + (h - self.BOX) // 2
        self.label.abs_rect = (lx, ly, self.label.rect[2], self.label.rect[3])
        saved = self.label._render_opacity
        self.label._render_opacity = self._render_opacity * self.label.opacity
        self.label.render(renderer)
        self.label._render_opacity = saved


class RadioGroup(Panel):
    """单选组：垂直 / 水平排列圆点选项。"""

    def __init__(
        self,
        rect,
        options,
        selected_index: int = 0,
        on_select=None,
        factory=None,
        horizontal: bool = False,
        id=None,
        layer: int = 0,
        layout_weight: int = 0,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        layout = (
            HBoxLayout(spacing=8, padding=(0, 0, 0, 0)) if horizontal
            else VBoxLayout(spacing=4, padding=(0, 0, 0, 0))
        )
        super().__init__(
            rect, layout=layout, parent=parent, visible=visible, enabled=enabled
        )
        self.id = id
        self.layer = layer
        self.layout_weight = layout_weight
        self.options = list(options)
        self.selected_index = 0
        self.on_select = on_select      # 点击后回调 on_select(index, text)
        self._buttons = []
        for i, text in enumerate(self.options):
            btn = _RadioButton(self, i, text, factory, (0, 0, -1, 28))
            self._buttons.append(btn)
            self.add_child(btn)
        # 初始选中（不触发回调）
        idx = selected_index if 0 <= selected_index < len(self.options) else 0
        self.set_selected(idx)

    # ---- 交互 ----

    def select(self, index: int) -> None:
        """选中指定索引（内部点击路径），并触发 on_select(index, text)。"""
        if not (0 <= index < len(self.options)):
            return
        self.selected_index = index
        self.mark_dirty()
        for i, btn in enumerate(self._buttons):
            btn.set_checked(i == index)
        if self.on_select is not None:
            self.on_select(index, self.options[index])

    def set_selected(self, index: int) -> None:
        """外部程序主动切换选中项（不触发 on_select）。"""
        if not (0 <= index < len(self.options)):
            return
        self.selected_index = index
        self.mark_dirty()
        for i, btn in enumerate(self._buttons):
            btn.set_checked(i == index)

    def get_selected(self):
        """返回当前 (index, text)。"""
        return self.selected_index, self.options[self.selected_index]
