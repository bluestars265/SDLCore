# -*- coding: utf-8 -*-
"""ComboBox：下拉选择框控件（继承 Widget）。

- 头部：矩形框（带边框）+ 左侧当前选中文本 + 右侧倒三角。
- 下拉列表：单选 ``ListBox``，浮于界面最上层——通过 UIManager 的
  ``root_panel`` 挂载（带高 ``layer``），避免被其他容器（如 ScrollPanel）裁剪。
- 交互：点击头部展开/收起；选择项后收起并回调 ``on_select(text, index)``；
  点击外部自动收起。
- 收起 / 禁用时从父容器移除动态下拉 Panel，防止泄漏与悬空渲染。
"""

import sdl2

from SDLCore.ui.widget import Widget
from SDLCore.ui.panel import Panel
from SDLCore.ui.label import Label
from SDLCore.ui.listbox import ListBox
from SDLCore.ui.layout import Constraints
from SDLCore.ui import apply_opacity


class ComboBox(Widget):
    """下拉选择框控件。"""

    COLOR_BG = (255, 255, 255, 255)
    COLOR_BORDER = (120, 120, 120, 255)
    COLOR_TEXT = (30, 30, 30, 255)
    COLOR_ARROW = (80, 80, 80, 255)
    DROPDOWN_COLOR = (40, 40, 40, 240)
    DROPDOWN_MAX_H = 150
    ITEM_H = 30
    TEXT_PAD = 6

    def __init__(
        self,
        rect,
        items,
        selected_index: int = 0,
        on_select=None,
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
        self.items = list(items)
        self.selected_index = max(
            0, min(int(selected_index), len(self.items) - 1)
        ) if self.items else 0
        self.on_select = on_select      # 选择后回调 on_select(text, index)
        self.factory = factory
        self._expanded = False
        self._dropdown_panel = None
        self._dropdown_listbox = None

        # 头部文本
        self.label = None
        if factory is not None:
            self.label = Label(
                (self.TEXT_PAD, 0, 0, 0), text=self._current_text(),
                color=self.COLOR_TEXT, font_size="14px", factory=factory,
            )

    def _current_text(self) -> str:
        if not self.items:
            return ""
        return self.items[self.selected_index]

    # ---- 下拉管理 ----

    def _get_manager(self):
        node = self
        while node is not None:
            manager = getattr(node, "_manager", None)
            if manager is not None:
                return manager
            node = getattr(node, "parent", None)
        return None

    def _open_dropdown(self) -> None:
        if self._expanded or not self.enabled:
            return
        manager = self._get_manager()
        if manager is None:
            return
        x, y, w, h = self.abs_rect
        drop_h = min(self.DROPDOWN_MAX_H, len(self.items) * self.ITEM_H)
        # 下拉容器：直接挂到 UIManager 的 root_panel（顶层），高 layer 浮于最上
        panel = Panel((x, y + h, w, drop_h), color=self.DROPDOWN_COLOR)
        panel.layer = self.layer + 100
        lb = ListBox(
            (0, 0, w, drop_h), items=self.items,
            allow_multi_select=False, factory=self.factory,
            on_selection_changed=self._on_dropdown_selected,
        )
        panel.add_child(lb)
        manager.root_panel.add_child(panel)
        self._dropdown_panel = panel
        self._dropdown_listbox = lb
        self._expanded = True

    def _close_dropdown(self) -> None:
        if self._dropdown_panel is not None:
            parent = self._dropdown_panel.parent
            if parent is not None:
                parent.remove_child(self._dropdown_panel)
        self._dropdown_panel = None
        self._dropdown_listbox = None
        self._expanded = False

    def _on_dropdown_selected(self, texts) -> None:
        if texts:
            text = texts[0]
            index = self.items.index(text)
            self.selected_index = index
            self.mark_dirty()
            if self.label is not None:
                self.label.set_text(text)
            if self.on_select is not None:
                self.on_select(text, index)
        self._close_dropdown()

    # ---- 事件 ----

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if (
            event.type == sdl2.SDL_MOUSEBUTTONDOWN
            and event.button.button == sdl2.SDL_BUTTON_LEFT
        ):
            px, py = event.button.x, event.button.y
            if self._contains(px, py):
                # 点击头部：切换展开/收起
                if self._expanded:
                    self._close_dropdown()
                else:
                    self._open_dropdown()
                return True
            if self._expanded:
                # 点击头部外部（下拉内部由下拉 ListBox 消费）：收起
                self._close_dropdown()
        return False

    # ---- 启用/禁用 ----

    def set_enabled(self, enabled: bool) -> None:
        """禁用时收起下拉并关闭交互。"""
        self.enabled = bool(enabled)
        if not self.enabled:
            self._close_dropdown()

    # ---- 渲染 ----

    def _draw_arrow(self, renderer, cx: int, cy: int) -> None:
        # 倒三角（▾）
        color = apply_opacity(self.COLOR_ARROW, self._render_opacity)
        renderer.draw_line([(cx - 5, cy - 2), (cx, cy + 3)], color)
        renderer.draw_line([(cx, cy + 3), (cx + 5, cy - 2)], color)

    def render(self, renderer) -> None:
        if not self.visible:
            return
        x, y, w, h = self.abs_rect
        # 头部背景 + 边框
        renderer.fill((x, y, w, h),
                      apply_opacity(self.COLOR_BG, self._render_opacity))
        renderer.draw_rect((x, y, w, h),
                           apply_opacity(self.COLOR_BORDER, self._render_opacity))
        # 当前文本（透明度传播）
        if self.label is not None:
            self.label.set_text(self._current_text())
            tw, th = self.label.measure(Constraints())
            self.label.abs_rect = (x + self.TEXT_PAD, y + (h - th) // 2, tw, th)
            saved = self.label._render_opacity
            self.label._render_opacity = (
                self._render_opacity * self.label.opacity
            )
            self.label.render(renderer)
            self.label._render_opacity = saved
        # 右侧倒三角
        cx = x + w - 12
        cy = y + h // 2
        self._draw_arrow(renderer, cx, cy)

    def __del__(self):
        try:
            self._close_dropdown()
        except Exception:  # noqa: BLE001
            pass
