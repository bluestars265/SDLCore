# -*- coding: utf-8 -*-
"""Button：可点击按钮控件。

- 三种状态：NORMAL / HOVER / PRESSED，对应不同背景色。
- 鼠标左键在按钮内按下 → PRESSED；在按钮内释放 → 触发 ``callback`` 并恢复 NORMAL。
- 绘制：按当前状态填充颜色矩形 + 2px 黑色边框。
"""

import ctypes
import enum

import sdl2

from SDLCore.ui.widget import Widget
from SDLCore.ui import apply_opacity


class ButtonState(enum.Enum):
    """按钮的交互状态。"""

    NORMAL = enum.auto()
    HOVER = enum.auto()
    PRESSED = enum.auto()


class Button(Widget):
    COLOR_NORMAL = (160, 160, 160, 255)      # 灰色
    COLOR_HOVER = (135, 206, 250, 255)       # 浅蓝
    COLOR_PRESSED = (25, 60, 130, 255)       # 深蓝
    COLOR_BORDER = (0, 0, 0, 255)            # 黑色边框
    BORDER_WIDTH = 2                         # 边框线宽（px）

    def __init__(
        self,
        rect,
        text: str = "",
        callback=None,
        fit_content: bool = False,
        font_size="14px",
        padding=(12, 6),
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        super().__init__(rect, parent=parent, visible=visible, enabled=enabled)
        self.text = text                      # 文字暂存，本阶段不渲染文字
        self.callback = callback              # 点击时回调函数
        self.state = ButtonState.NORMAL
        self.fit_content = fit_content        # 是否按文字内容自动测量尺寸
        self.font_size = font_size            # 用于测量文字的字体字号
        self.padding = tuple(padding)         # 文字内边距（fit_content 用）
        self._font = None                     # 懒加载字体（仅测量用）

    # ---- 配置接口 ----

    def set_text(self, text: str) -> None:
        """更新按钮文字（当前仅存储，本阶段不渲染文字）。"""
        self.text = text

    def set_callback(self, callback) -> None:
        """设置点击回调函数（点击释放时调用）。"""
        self.callback = callback

    # ---- 内部工具 ----

    def _contains(self, px: int, py: int) -> bool:
        x, y, w, h = self.abs_rect
        return x <= px < x + w and y <= py < y + h

    # ---- 事件处理 ----

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False

        if event.type == sdl2.SDL_MOUSEMOTION:
            self._update_hover(event.motion.x, event.motion.y)
            if self._hovered:
                self.state = ButtonState.HOVER
            elif self.state != ButtonState.NORMAL:
                self.state = ButtonState.NORMAL
            # 鼠标移动不独占：返回 False，让下层控件也能同步更新状态
            return False

        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if (
                event.button.button == sdl2.SDL_BUTTON_LEFT
                and self._contains(event.button.x, event.button.y)
            ):
                self.state = ButtonState.PRESSED
                return True
            return False

        if event.type == sdl2.SDL_MOUSEBUTTONUP:
            if (
                event.button.button == sdl2.SDL_BUTTON_LEFT
                and self.state == ButtonState.PRESSED
            ):
                self.state = ButtonState.NORMAL
                # 仅在按钮内释放才触发回调（拖出释放则不触发）
                if self._contains(event.button.x, event.button.y):
                    if self.callback is not None:
                        self.callback()
                    return True
            return False

        return False

    # ---- 测量（fit_content） ----

    def _ensure_font(self) -> bool:
        if self._font is None:
            from sdl2.ext.ttf import FontTTF
            from SDLCore.ui import find_font
            path = find_font()
            if path is None:
                return False
            self._font = FontTTF(path, self.font_size, (0, 0, 0, 255))
        return True

    def _measure_text(self, text: str) -> int:
        if not text or not self._ensure_font():
            return 0
        font = self._font.get_ttf_font("default")
        w = ctypes.c_int(0)
        h = ctypes.c_int(0)
        sdl2.sdlttf.TTF_SizeUTF8(
            font, text.encode("utf-8"), ctypes.byref(w), ctypes.byref(h)
        )
        return w.value

    def _font_height(self) -> int:
        if not self._ensure_font():
            return 0
        return sdl2.sdlttf.TTF_FontHeight(self._font.get_ttf_font("default"))

    def measure(self, constraints=None):
        """fit_content 时按文字 + 内边距计算；否则回退基类（hint 尺寸）。"""
        from SDLCore.ui.layout import Constraints
        if constraints is None:
            constraints = Constraints()
        if self.fit_content and self.text:
            w = self._measure_text(self.text) + self.padding[0] * 2
            h = self._font_height() + self.padding[1] * 2
            return (constraints.clamp_w(w), constraints.clamp_h(h))
        return super().measure(constraints)

    # ---- 渲染 ----

    def render(self, renderer) -> None:
        if not self.visible:
            return
        color = {
            ButtonState.NORMAL: self.COLOR_NORMAL,
            ButtonState.HOVER: self.COLOR_HOVER,
            ButtonState.PRESSED: self.COLOR_PRESSED,
        }[self.state]
        renderer.fill(
            self.abs_rect, apply_opacity(color, self._render_opacity)
        )

        # 黑色边框：绘制外层 + 逐层内缩的矩形，凑出 BORDER_WIDTH 线宽
        x, y, w, h = self.abs_rect
        for i in range(self.BORDER_WIDTH):
            renderer.draw_rect(
                (x + i, y + i, w - 2 * i, h - 2 * i),
                apply_opacity(self.COLOR_BORDER, self._render_opacity),
            )
