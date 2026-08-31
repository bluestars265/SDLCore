# -*- coding: utf-8 -*-
"""ListBox：列表选择控件（继承 ScrollPanel，支持多选）。

- 内部 ``content`` 使用 ``VBoxLayout``，每个 Item 为 ``Panel``（背景色可切换）包裹 ``Label``。
- Item 高度固定 30px、宽度填满父容器（``w=-1``）。
- 交互（模拟 Ctrl/Shift）：
  - 单击：选中当前项；
  - Ctrl+单击：切换当前项选中状态（不影响其他项）；
  - Shift+单击：选中从锚点（上次点击项）到当前项的范围。
- 选中项背景高亮，未选中透明/浅灰。
- 滚轮滚动由父类 ScrollPanel 提供；Item 点击消费事件不冒泡误触。
"""

import sdl2

from SDLCore.ui.scrollpanel import ScrollPanel
from SDLCore.ui.panel import Panel
from SDLCore.ui.label import Label
from SDLCore.ui.layout import VBoxLayout


class _ListBoxItem(Panel):
    """单个列表项：Panel 背景 + Label 文本。"""

    HEIGHT = 30
    PAD = 6
    COLOR_SELECTED = (30, 120, 200, 150)   # 选中高亮（半透明蓝）
    COLOR_NORMAL = (0, 0, 0, 0)            # 未选中透明
    COLOR_TEXT = (220, 220, 220, 255)

    def __init__(self, listbox, index, text, factory):
        super().__init__((0, 0, -1, self.HEIGHT), color=self.COLOR_NORMAL)
        self.listbox = listbox
        self.index = index
        self.text = text
        self.selected = False
        self.label = Label(
            (self.PAD, (self.HEIGHT - 20) // 2, 0, 20),
            text=text, color=self.COLOR_TEXT, font_size="14px", factory=factory,
        )
        self.add_child(self.label)

    def set_selected(self, selected: bool) -> None:
        self.selected = bool(selected)
        self.color = self.COLOR_SELECTED if selected else self.COLOR_NORMAL

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if (
            event.type == sdl2.SDL_MOUSEBUTTONDOWN
            and event.button.button == sdl2.SDL_BUTTON_LEFT
            and self._contains(event.button.x, event.button.y)
        ):
            # 实时键盘修饰键状态（Ctrl / Shift）
            mod = sdl2.SDL_GetModState()
            ctrl = bool(mod & sdl2.KMOD_CTRL)
            shift = bool(mod & sdl2.KMOD_SHIFT)
            self.listbox._on_item_click(self.index, ctrl, shift)
            return True  # 消费事件，避免冒泡误触其他项
        return super().handle_event(event)


class ListBox(ScrollPanel):
    """列表选择控件（支持多选 / Ctrl / Shift）。"""

    def __init__(
        self,
        rect,
        items,
        allow_multi_select: bool = True,
        on_selection_changed=None,
        factory=None,
        id=None,
        layer: int = 0,
        layout_weight: int = 0,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        super().__init__(rect, content_size=None, parent=parent,
                         visible=visible, enabled=enabled)
        self.id = id
        self.layer = layer
        self.layout_weight = layout_weight
        self.items = list(items)
        self.allow_multi_select = allow_multi_select
        self.on_selection_changed = on_selection_changed  # 回调接收选中 items 列表
        self.factory = factory
        self._selected = set()    # 选中项索引集合
        self._anchor = -1         # Shift 范围锚点
        self._last_click = -1

        # content 使用 VBoxLayout 垂直排列，宽度填满视口
        self.content.set_layout(VBoxLayout(spacing=0, padding=(0, 0, 0, 0)))
        self.content.set_rect((0, 0, self.rect[2], 0))  # 内容宽 = 视口宽
        for i, text in enumerate(self.items):
            self.add_child(_ListBoxItem(self, i, text, factory))
        self._refresh_items()

    def set_rect(self, rect) -> None:
        """随视口尺寸变化更新内容宽度并重新排布 Item。"""
        super().set_rect(rect)
        self._content_w = self.rect[2]
        # 同步 content 宽度（可能为 -1 填满标记）并重排 items
        self.content.rect = (
            self.content.rect[0], self.content.rect[1],
            self._content_w, self._content_h,
        )
        if self.content.layout is not None:
            self.content.layout.layout(self.content)

    # ---- 交互 ----

    def _on_item_click(self, index: int, ctrl: bool, shift: bool) -> None:
        if self.allow_multi_select:
            if shift:
                # 范围选择：从锚点到当前项
                anchor = self._anchor if self._anchor >= 0 else self._last_click
                if anchor < 0:
                    anchor = index
                lo, hi = min(anchor, index), max(anchor, index)
                self._selected = set(range(lo, hi + 1))
            elif ctrl:
                # 切换当前项
                if index in self._selected:
                    self._selected.discard(index)
                else:
                    self._selected.add(index)
            else:
                # 单击：单选当前项
                self._selected = {index}
        else:
            # 单选模式：忽略 Ctrl/Shift，直接选中当前项
            self._selected = {index}
        self._last_click = index
        if not shift:
            self._anchor = index
        self._refresh_items()
        self._fire_selection_changed()

    def _refresh_items(self) -> None:
        self.mark_dirty()
        for i, child in enumerate(self.content.children):
            child.set_selected(i in self._selected)

    def _fire_selection_changed(self) -> None:
        if self.on_selection_changed is not None:
            texts = [self.items[i] for i in sorted(self._selected)]
            self.on_selection_changed(texts)

    # ---- 接口 ----

    def set_items(self, new_items) -> None:
        """刷新列表（清空选中状态）。"""
        self.items = list(new_items)
        self._selected.clear()
        self._anchor = -1
        self._last_click = -1
        # 清空旧项
        for child in list(self.content.children):
            self.content.remove_child(child)
        for i, text in enumerate(self.items):
            self.add_child(_ListBoxItem(self, i, text, self.factory))
        self._refresh_items()

    def get_selected(self):
        """返回当前选中的文本列表。"""
        return [self.items[i] for i in sorted(self._selected)]

    def get_selected_indices(self) -> list:
        """返回当前选中的索引列表。"""
        return sorted(self._selected)
