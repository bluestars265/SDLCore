# -*- coding: utf-8 -*-
"""Panel：容器控件，用于组合子控件。

- 子控件的 ``rect`` 是相对 Panel 的坐标；
  渲染时通过 ``abs_rect``（由 ``update_abs_position`` 递归计算）转为世界绝对坐标。
- 默认背景为半透明灰色，可通过 ``color`` 参数自定义。
- 可持有 ``Layout`` 实例（如 GridLayout / VBoxLayout / HBoxLayout），
  在 add_child / remove_child / set_rect 时自动排布子控件。
"""

from SDLCore.ui.widget import Widget
from SDLCore.ui import enable_alpha_blend, apply_opacity


class Panel(Widget):
    """纯粹的容器：绘制自身背景色后，依次渲染所有可见子控件。"""

    DEFAULT_BG_COLOR = (30, 30, 30, 200)

    def __init__(
        self,
        rect,
        color=DEFAULT_BG_COLOR,
        layout=None,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        super().__init__(rect, parent=parent, visible=visible, enabled=enabled)
        self.color = tuple(color)
        self._layout = layout       # 布局对象（None 表示无布局，子控件自由定位）

    # ---- 布局 ----

    def set_layout(self, layout) -> None:
        """设置布局对象，并立即排布现有子控件。"""
        self._layout = layout
        if layout is not None:
            layout.layout(self)

    @property
    def layout(self):
        """当前布局对象（无则为 None）。"""
        return self._layout

    def add_child(self, widget) -> Widget:
        super().add_child(widget)
        if self._layout is not None:
            self._layout.layout(self)
        return widget

    def remove_child(self, widget) -> None:
        super().remove_child(widget)
        if self._layout is not None:
            self._layout.layout(self)

    def set_rect(self, rect) -> None:
        super().set_rect(rect)
        if self._layout is not None:
            self._layout.layout(self)

    def handle_event(self, event) -> bool:
        """容器自身不消费事件，但需递归分发给子控件（按图层上层优先，消费即停止）。"""
        if not self.visible or not self.enabled:
            return False
        # layer 大的控件在更上层，先接收事件；稳定排序保证同层保持添加顺序
        for child in reversed(sorted(self.children, key=lambda c: c.layer)):
            if child.visible and child.enabled:
                if child.handle_event(event):
                    return True
        return False

    def _render_child(self, child, renderer) -> None:
        """渲染子控件并传播透明度（父有效透明度 × 子透明度）。"""
        saved = child._render_opacity
        child._render_opacity = self._render_opacity * child.opacity
        child.render(renderer)
        child._render_opacity = saved

    def render(self, renderer) -> None:
        if not self.visible:
            return
        enable_alpha_blend(renderer)
        renderer.fill(
            self.abs_rect,
            apply_opacity(self.color, self._render_opacity),
        )
        # layer 大的控件绘制在上层；稳定排序保证同层保持添加顺序
        for child in sorted(self.children, key=lambda c: c.layer):
            if child.visible:
                self._render_child(child, renderer)
