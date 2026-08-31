# -*- coding: utf-8 -*-
"""Widget：GUI 控件基类（通用引擎层，与具体游戏无关）。

坐标约定：
- ``rect`` 存 (x, y, w, h)，为**相对父容器的坐标**。
- ``abs_rect`` 为渲染/事件使用的**世界绝对坐标**，
  由父容器在 ``update_abs_position`` 中递归计算。

所有控件统一遵循以下通用接口：
- 定位 / 尺寸：``set_rect`` / ``set_position`` / ``set_size``
- 可见 / 可用：``set_visible`` / ``set_enabled``
- 容器：``add_child`` / ``remove_child``（任何控件均可挂载子控件）
- 生命周期：``update_abs_position`` / ``handle_event`` / ``update`` / ``render``
- 悬停：``_update_hover`` 维护 ``_hovered`` 状态，进入/离开时调用 ``on_mouse_enter`` / ``on_mouse_leave``
"""

import sdl2

from SDLCore.ui.layout import Constraints


class Widget:
    """所有 UI 控件的抽象基类。"""

    def __init__(
        self,
        rect,
        id=None,
        layer: int = 0,
        layout_weight: int = 0,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        self.rect = tuple(rect)          # 相对父容器的坐标 (x, y, w, h)
        self._hint_rect = tuple(rect)    # 原始布局意图（含 -1 自适应标记，布局系统读取）
        self.id = id                     # 全局唯一标识（便于查找/调试，默认 None）
        self.layer = layer               # 图层（z-index），越大越靠上层
        self.layout_weight = layout_weight  # flex 权重（VBox/HBox 分配剩余空间）
        self.parent = parent             # 父容器（Widget 或 None）
        self.children: list["Widget"] = []
        self.visible = visible
        self.enabled = enabled
        self.abs_rect = self.rect        # 世界绝对坐标 (x, y, w, h)
        self._hovered = False            # 鼠标是否悬停在控件上
        self._dirty = True               # 重绘标记（状态/内容变化时置脏）
        self.opacity = 1.0               # 控件透明度（0.0 ~ 1.0）
        self._render_opacity = 1.0       # 渲染有效透明度（父透明度 × 自身透明度）

    def set_opacity(self, opacity: float) -> None:
        """设置控件透明度（0.0 全透明 ~ 1.0 不透明）。

        同步渲染透明度：独立控件直接生效；处于容器内时，
        渲染时会被父级透明度调制覆盖为有效值。
        """
        self.opacity = max(0.0, min(1.0, float(opacity)))
        self._render_opacity = self.opacity
        self.mark_dirty()

    def mark_dirty(self) -> None:
        """标记需要重绘（状态 / 内容 / 尺寸变化时调用）。"""
        self._dirty = True

    # ---- 坐标系统 ----

    def update_abs_position(self, parent_abs_x: int = 0, parent_abs_y: int = 0) -> None:
        """递归刷新绝对坐标：abs = parent_abs + 自身相对坐标。"""
        x, y, w, h = self.rect
        self.abs_rect = (parent_abs_x + x, parent_abs_y + y, w, h)
        for child in self.children:
            child.update_abs_position(self.abs_rect[0], self.abs_rect[1])

    def _contains(self, px: int, py: int) -> bool:
        """判断世界坐标点 (px, py) 是否落在控件绝对矩形内。"""
        x, y, w, h = self.abs_rect
        return x <= px < x + w and y <= py < y + h

    # ---- 悬停跟踪 ----

    def _update_hover(self, px: int, py: int) -> None:
        """更新悬停状态：鼠标进入/离开控件时调用对应钩子。"""
        inside = self._contains(px, py)
        if inside and not self._hovered:
            self._hovered = True
            self.on_mouse_enter()
        elif not inside and self._hovered:
            self._hovered = False
            self.on_mouse_leave()

    def on_mouse_enter(self) -> None:
        """鼠标进入控件时调用（子类可重写，例如显示提示框）。"""

    def on_mouse_leave(self) -> None:
        """鼠标离开控件时调用（子类可重写）。"""

    # ---- 定位 / 尺寸 ----

    def set_rect(self, rect) -> None:
        """设置相对坐标矩形 (x, y, w, h)，并刷新本控件及子控件绝对坐标。"""
        self.rect = tuple(rect)
        self.mark_dirty()
        if self.parent is not None:
            px, py = self.parent.abs_rect[0], self.parent.abs_rect[1]
            self.update_abs_position(px, py)
        else:
            self.abs_rect = self.rect
            for child in self.children:
                child.update_abs_position(self.abs_rect[0], self.abs_rect[1])

    def set_position(self, x: int, y: int) -> None:
        """设置相对坐标位置（保持宽高不变）。"""
        self.set_rect((x, y, self.rect[2], self.rect[3]))

    def set_size(self, w: int, h: int) -> None:
        """设置宽高（保持相对位置不变）。"""
        self.set_rect((self.rect[0], self.rect[1], w, h))

    # ---- 可见性 / 可用性 ----

    def set_visible(self, visible: bool) -> None:
        """设置是否渲染与接收事件。"""
        self.visible = visible
        self.mark_dirty()

    def set_enabled(self, enabled: bool) -> None:
        """设置是否可用（禁用后不接收事件）。"""
        self.enabled = enabled
        self.mark_dirty()

    # ---- 容器接口（任何控件均可挂载子控件） ----

    def add_child(self, widget) -> "Widget":
        """挂载子控件，并立即刷新其绝对坐标。"""
        widget.parent = self
        self.children.append(widget)
        widget.update_abs_position(self.abs_rect[0], self.abs_rect[1])
        return widget

    def remove_child(self, widget) -> None:
        """移除子控件并解除父子关系。"""
        if widget in self.children:
            self.children.remove(widget)
            widget.parent = None

    # ---- 生命周期 ----

    def handle_event(self, event) -> bool:
        """处理一个 SDL 事件。返回 True 表示消费该事件（停止传递）。"""
        if not self.visible or not self.enabled:
            return False
        if event.type == sdl2.SDL_MOUSEMOTION:
            self._update_hover(event.motion.x, event.motion.y)
        return False

    def update(self, delta_time: float) -> None:
        """每帧更新（子类可重写，如 InputBox 光标闪烁与 IME 定位）。"""
        pass

    def measure(self, constraints: Constraints | None = None):
        """根据约束与布局意图（hint_rect）返回首选尺寸 (w, h)。

        约束由父布局器传入；``w/h == -1`` 表示填满可用尺寸（max），
        固定值表示首选尺寸，``0`` 则由子类按内容计算（fit_content）。
        """
        if constraints is None:
            constraints = Constraints()
        w = self._hint_rect[2]
        h = self._hint_rect[3]
        if w == -1:
            w = constraints.max_w
        if h == -1:
            h = constraints.max_h
        return (constraints.clamp_w(w), constraints.clamp_h(h))

    def render(self, renderer) -> None:
        """由子类实现具体绘制逻辑。"""
        pass

