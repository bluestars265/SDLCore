# -*- coding: utf-8 -*-
"""UIManager：UI 总控。

- ``root_panel`` 为铺满全屏的透明顶层容器，通过 ``resize`` 随窗口尺寸实时更新。
- 事件分发采用**逆序**遍历（从最上层开始），控件消费事件（返回 True）即停止传递。
- 无坐标的 IME 文本事件（``SDL_TEXTINPUT`` / ``SDL_TEXTEDITING``）直接发送给
  当前持有焦点的 ``InputBox``（``self.focused_widget``）。
"""

import sdl2

from SDLCore.ui.panel import Panel


class UIManager:
    """UI 管理器：负责全屏根容器、事件分发与整体渲染。"""

    INTERESTED_EVENTS = (
        sdl2.SDL_MOUSEMOTION,
        sdl2.SDL_MOUSEBUTTONDOWN,
        sdl2.SDL_MOUSEBUTTONUP,
        sdl2.SDL_MOUSEWHEEL,
        sdl2.SDL_KEYDOWN,
        sdl2.SDL_KEYUP,
    )
    # IME 文本事件：无坐标，只发给焦点控件
    TEXT_EVENTS = (sdl2.SDL_TEXTINPUT, sdl2.SDL_TEXTEDITING)

    def __init__(self) -> None:
        # 透明根面板：铺满全屏，仅作为顶层容器
        self.root_panel = Panel((0, 0, 0, 0), color=(0, 0, 0, 0))
        self.root_panel._manager = self  # 供子控件沿父链找到本管理器
        self.focused_widget = None       # 当前持有输入焦点的控件（如 InputBox）

    def set_focus(self, widget) -> None:
        """注册/清空焦点控件（传入 None 表示失去焦点）。"""
        self.focused_widget = widget

    def resize(self, width: int, height: int) -> None:
        """更新根面板铺满全屏，并递归刷新所有子控件的绝对坐标。"""
        self.root_panel.rect = (0, 0, int(width), int(height))
        self.root_panel.update_abs_position(0, 0)

    def handle_events(self, events) -> None:
        """分发事件：IME 文本事件直达焦点控件；其余按图层上层优先分发，消费即停止。"""
        for event in events:
            if event.type in self.TEXT_EVENTS:
                if self.focused_widget is not None:
                    self.focused_widget.handle_event(event)
                continue
            if event.type in self.INTERESTED_EVENTS:
                # 键盘事件优先交给焦点控件（输入框接收回车/退格/方向键等）
                if event.type in (sdl2.SDL_KEYDOWN, sdl2.SDL_KEYUP):
                    if (
                        self.focused_widget is not None
                        and self.focused_widget.enabled
                        and self.focused_widget.handle_event(event)
                    ):
                        continue
                # 按图层（layer）上层优先分发
                for child in reversed(
                    sorted(self.root_panel.children, key=lambda c: c.layer)
                ):
                    if child.handle_event(event):
                        break

    def find_by_id(self, widget_id):
        """在整棵 UI 树中按 id 递归查找控件；未找到返回 None。"""
        return self._find_recursive(self.root_panel, widget_id)

    def _find_recursive(self, widget, widget_id):
        if widget.id == widget_id:
            return widget
        for child in widget.children:
            found = self._find_recursive(child, widget_id)
            if found is not None:
                return found
        return None

    def update(self, delta_time: float) -> None:
        """递归遍历 UI 树，调用各控件的 update（如 InputBox 光标闪烁与 IME 定位）。"""
        self._update_recursive(self.root_panel, delta_time)

    def _update_recursive(self, widget, delta_time) -> None:
        widget.update(delta_time)
        for child in widget.children:
            self._update_recursive(child, delta_time)

    def render(self, renderer) -> None:
        """渲染整棵 UI 树（经 BatchedRenderer 合批不透明矩形）。"""
        from SDLCore.ui.batcher import BatchedRenderer
        batched = BatchedRenderer(renderer)
        self.root_panel.render(batched)
        batched.flush()
