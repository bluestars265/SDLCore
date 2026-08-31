# -*- coding: utf-8 -*-
"""CheckBox：复选框控件（继承 Widget）。

- 内部组合 ``Label`` 显示文本（位于方框右侧、垂直居中）。
- 方框绘制在控件矩形左边缘、垂直居中。
- 鼠标左键在控件矩形内点击时切换 ``checked``，并调用 ``callback(checked)``。
- 选中态：黑色边框 + 主题色填充 + 白色对勾；未选中态：灰色边框 + 白色内部。
- ``set_text`` / ``set_checked`` 支持运行时更新界面。
"""

import sdl2

from SDLCore.ui.widget import Widget
from SDLCore.ui.label import Label
from SDLCore.ui import apply_opacity


class CheckBox(Widget):
    """复选框控件。"""

    COLOR_BG = (255, 255, 255, 255)            # 未选中内部白色
    COLOR_BORDER = (120, 120, 120, 255)        # 未选中灰色边框
    COLOR_CHECKED = (30, 120, 200, 255)        # 选中主题色（蓝）
    COLOR_BORDER_CHECKED = (0, 0, 0, 255)      # 选中黑色边框
    COLOR_CHECK_MARK = (255, 255, 255, 255)    # 对勾白色
    COLOR_TEXT = (30, 30, 30, 255)             # 文本颜色

    BOX_SIZE = 20          # 方框边长（px）
    GAP = 6                # 方框与文本间距（px）
    LABEL_H = 20           # 文本行高参考（px）

    def __init__(
        self,
        rect,
        text: str = "",
        checked: bool = False,
        callback=None,
        factory=None,
        id=None,
        layer: int = 0,
        layout_weight: int = 0,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            rect,
            id=id,
            layer=layer,
            layout_weight=layout_weight,
            parent=parent,
            visible=visible,
            enabled=enabled,
        )
        self.text = text
        self.checked = bool(checked)
        self.callback = callback      # 点击切换后调用 callback(checked)

        # 内部文本 Label（位于方框右侧、垂直居中）
        self.label = Label(
            (self.BOX_SIZE + self.GAP, (self.rect[3] - self.LABEL_H) // 2,
             0, self.LABEL_H),
            text=text,
            color=self.COLOR_TEXT,
            font_size="14px",
            factory=factory,
        )
        self.label.layer = self.layer + 1  # 文本始终在方框之上

    # ---- 运行时更新 ----

    def set_text(self, text: str) -> None:
        """更新文本显示。"""
        self.text = text
        self.label.set_text(text)
        self.mark_dirty()

    def set_checked(self, checked: bool) -> None:
        """设置选中状态（不触发回调）。"""
        self.checked = bool(checked)
        self.mark_dirty()

    # ---- 测量（fit_content） ----

    def measure(self, constraints=None):
        """首选尺寸：方框 + 间距 + 文字宽。"""
        from SDLCore.ui.layout import Constraints
        if constraints is None:
            constraints = Constraints()
        tw = self.label.measure(constraints)[0] if self.text else 0
        w = self.BOX_SIZE + self.GAP + tw
        h = max(self.BOX_SIZE, self._hint_rect[3])
        return (constraints.clamp_w(w), constraints.clamp_h(h))

    # ---- 事件 ----

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if (
            event.type == sdl2.SDL_MOUSEBUTTONDOWN
            and event.button.button == sdl2.SDL_BUTTON_LEFT
            and self._contains(event.button.x, event.button.y)
        ):
            self.checked = not self.checked
            if self.callback is not None:
                self.callback(self.checked)
            return True
        return False

    # ---- 渲染 ----

    def render(self, renderer) -> None:
        if not self.visible:
            return
        x, y, w, h = self.abs_rect
        op = self._render_opacity
        box = self.BOX_SIZE
        bx = x
        by = y + (h - box) // 2

        # 方框背景
        bg = self.COLOR_CHECKED if self.checked else self.COLOR_BG
        renderer.fill((bx, by, box, box), apply_opacity(bg, op))
        # 方框边框
        border = self.COLOR_BORDER_CHECKED if self.checked else self.COLOR_BORDER
        renderer.draw_rect((bx, by, box, box), apply_opacity(border, op))
        # 选中态：白色对勾（两条线）
        if self.checked:
            mark = apply_opacity(self.COLOR_CHECK_MARK, op)
            mid = int(box * 0.4)
            renderer.draw_line(
                [(bx + 4, by + box // 2), (bx + mid, by + box - 5)], mark,
            )
            renderer.draw_line(
                [(bx + mid, by + box - 5), (bx + box - 4, by + 4)], mark,
            )

        # 文本 Label（动态垂直居中，透明度传播）
        lx = x + box + self.GAP
        ly = y + (h - self.LABEL_H) // 2
        self.label.abs_rect = (lx, ly, self.label.rect[2], self.label.rect[3])
        saved = self.label._render_opacity
        self.label._render_opacity = self._render_opacity * self.label.opacity
        self.label.render(renderer)
        self.label._render_opacity = saved
