# -*- coding: utf-8 -*-
"""Slider：滑动条控件（继承 Widget）。

- 背景轨道从控件左边缘延伸到右边缘；滑块垂直居中（``_thumb_rect`` 维护）。
- 交互：
  1. 鼠标点击轨道：按点击 X 对应比例设置 ``value``，并调用 ``on_value_changed``。
  2. 鼠标拖拽滑块：按下（DOWN）开始、移动（MOTION）更新、释放（UP）结束。
- 数值按 ``step`` 步长四舍五入对齐，并钳制在 ``[min_val, max_val]``。
- 渲染：灰色轨道 + 起点到滑块的填充条 + 滑块 + 滑块上方当前数值文本。
"""

import sdl2

from SDLCore.ui.widget import Widget
from SDLCore.ui.label import Label
from SDLCore.ui.layout import Constraints
from SDLCore.ui import apply_opacity


class Slider(Widget):
    """水平滑动条控件。"""

    TRACK_H = 6
    THUMB_W = 14
    THUMB_H = 20
    COLOR_TRACK = (120, 120, 120, 255)
    COLOR_FILL = (30, 120, 200, 255)
    COLOR_THUMB = (60, 60, 60, 255)
    COLOR_THUMB_EDGE = (30, 30, 30, 255)
    COLOR_TEXT = (255, 255, 255, 255)

    def __init__(
        self,
        rect,
        min_val: float = 0.0,
        max_val: float = 100.0,
        value: float = 0.0,
        step: float = 1.0,
        on_value_changed=None,
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
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        if self.max_val <= self.min_val:
            self.max_val = self.min_val + 1.0
        self.step = float(step)
        self.on_value_changed = on_value_changed  # 回调接收当前 value
        self.value = self._clamp(value)

        self._thumb_rect = (0, 0, self.THUMB_W, self.THUMB_H)  # 滑块矩形（绝对）
        self._dragging = False
        self._update_thumb_rect()  # 基于初始 value / abs_rect 初始化滑块位置

        # 当前数值文本（可选，需 factory）
        self.label = None
        if factory is not None:
            self.label = Label((0, 0, 0, 0), text="", color=self.COLOR_TEXT,
                               font_size="12px", factory=factory)

    # ---- 数值与坐标 ----

    def _clamp(self, v: float) -> float:
        return max(self.min_val, min(v, self.max_val))

    def _quantize(self, v: float) -> float:
        """按 step 步长四舍五入对齐。"""
        if self.step > 0:
            steps = round((v - self.min_val) / self.step)
            return self.min_val + steps * self.step
        return v

    def _apply_value(self, raw: float, fire: bool = True) -> None:
        value = self._clamp(self._quantize(raw))
        if value != self.value:
            self.value = value
            self.mark_dirty()
            self._update_thumb_rect()
            if fire and self.on_value_changed is not None:
                self.on_value_changed(value)

    def set_value(self, value: float) -> None:
        """外部程序设置数值（不触发回调）。"""
        self._apply_value(value, fire=False)

    def _update_thumb_rect(self) -> None:
        x, y, w, h = self.abs_rect
        span = self.max_val - self.min_val
        ratio = (self.value - self.min_val) / span if span > 0 else 0.0
        thumb_x = x + int((w - self.THUMB_W) * ratio)
        thumb_y = y + (h - self.THUMB_H) // 2
        self._thumb_rect = (thumb_x, thumb_y, self.THUMB_W, self.THUMB_H)

    def _set_value_from_x(self, px: int) -> None:
        x, y, w, h = self.abs_rect
        ratio = max(0.0, min(1.0, (px - x) / w)) if w > 0 else 0.0
        self._apply_value(self.min_val + ratio * (self.max_val - self.min_val))

    def _hit_thumb(self, px: int, py: int) -> bool:
        rx, ry, rw, rh = self._thumb_rect
        return rx <= px < rx + rw and ry <= py < ry + rh

    # ---- 事件 ----

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if event.button.button == sdl2.SDL_BUTTON_LEFT:
                if self._hit_thumb(event.button.x, event.button.y):
                    self._dragging = True
                    return True
                # 点击轨道：直接跳转到对应位置
                if self._contains(event.button.x, event.button.y):
                    self._set_value_from_x(event.button.x)
                    return True
            return False
        if event.type == sdl2.SDL_MOUSEMOTION:
            if self._dragging:
                self._set_value_from_x(event.motion.x)
                return True
            return False
        if event.type == sdl2.SDL_MOUSEBUTTONUP:
            if event.button.button == sdl2.SDL_BUTTON_LEFT and self._dragging:
                self._dragging = False
                return True
        return False

    # ---- 渲染 ----

    def _format_value(self) -> str:
        v = self.value
        return str(int(v)) if v == int(v) else f"{v:.1f}"

    def render(self, renderer) -> None:
        if not self.visible:
            return
        x, y, w, h = self.abs_rect
        self._update_thumb_rect()
        tx, ty, tw, th = self._thumb_rect
        op = self._render_opacity

        track_y = y + (h - self.TRACK_H) // 2
        # 灰色轨道
        renderer.fill((x, track_y, w, self.TRACK_H),
                      apply_opacity(self.COLOR_TRACK, op))
        # 起点到滑块中心的填充条
        fill_w = max(0, tx + tw // 2 - x)
        if fill_w > 0:
            renderer.fill((x, track_y, fill_w, self.TRACK_H),
                          apply_opacity(self.COLOR_FILL, op))
        # 滑块
        renderer.fill((tx, ty, tw, th), apply_opacity(self.COLOR_THUMB, op))
        renderer.draw_rect((tx, ty, tw, th),
                           apply_opacity(self.COLOR_THUMB_EDGE, op))

        # 当前数值文本（滑块正上方，透明度传播）
        if self.label is not None:
            self.label.set_text(self._format_value())
            tw2, th2 = self.label.measure(Constraints())
            cx = tx + tw // 2
            self.label.abs_rect = (cx - tw2 // 2, ty - th2 - 2, tw2, th2)
            saved = self.label._render_opacity
            self.label._render_opacity = self._render_opacity * self.label.opacity
            self.label.render(renderer)
            self.label._render_opacity = saved
