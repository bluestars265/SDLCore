# -*- coding: utf-8 -*-
"""Label：文本展示控件，支持不同颜色的文字渲染。

- 文字颜色通过 FontTTF 的具名样式（style）机制实现，可随时切换任意颜色。
- 文字以纹理精灵形式渲染，使用 TEXTURE 模式（GPU 硬件加速）。
"""

import ctypes

import sdl2
from sdl2.ext.ttf import FontTTF

from SDLCore.ui import find_font
from SDLCore.ui.widget import Widget


class Label(Widget):
    """展示不同颜色文字的标签控件。"""

    DEFAULT_COLOR = (255, 255, 255, 255)

    def __init__(
        self,
        rect,
        text: str = "",
        color=DEFAULT_COLOR,
        font_path=None,
        font_size="18px",
        parent=None,
        visible: bool = True,
        enabled: bool = True,
        factory=None,
    ) -> None:
        super().__init__(rect, parent=parent, visible=visible, enabled=enabled)
        self.text = text
        self.color = tuple(color)
        self.font_size = font_size

        # 字体：优先项目 resource/fonts/，回退系统字体
        font_path = font_path or find_font()
        if font_path is None:
            raise RuntimeError("未找到可用字体（resource/fonts/ 或系统字体）")
        self.font = FontTTF(font_path, font_size, self.color)

        self._color_styles = {self.color: "default"}  # 颜色 -> 具名样式
        self._style_counter = 1
        self._factory = None
        self._sprite = None
        self._cached = None
        if factory is not None:
            self.set_factory(factory)

    # ---- 配置 ----

    def set_factory(self, factory) -> None:
        """设置 TEXTURE 模式的 SpriteFactory（用于将文字 surface 转为纹理）。"""
        self._factory = factory

    def set_text(self, text: str) -> None:
        """更新显示文本。"""
        if text != self.text:
            self.text = text
            self._sprite = None

    def set_color(self, color) -> None:
        """更新文字颜色（首次出现的新颜色自动登记对应字体样式）。"""
        color = tuple(color)
        if color == self.color:
            return
        if color not in self._color_styles:
            name = "label_{0}".format(self._style_counter)
            self._style_counter += 1
            self.font.add_style(name, self.font_size, color)
            self._color_styles[color] = name
        self.color = color
        self._sprite = None

    # ---- 渲染 ----

    def _measure_text(self, text: str) -> int:
        """测量文字像素宽度（用于 fit_content）。"""
        if not text:
            return 0
        font = self.font.get_ttf_font("default")
        w = ctypes.c_int(0)
        h = ctypes.c_int(0)
        sdl2.sdlttf.TTF_SizeUTF8(
            font, text.encode("utf-8"), ctypes.byref(w), ctypes.byref(h)
        )
        return w.value

    def _font_height(self) -> int:
        return sdl2.sdlttf.TTF_FontHeight(self.font.get_ttf_font("default"))

    def measure(self, constraints=None):
        """首选尺寸：宽度按文字内容（fit_content），高度用 hint 固定或字体行高。"""
        from SDLCore.ui.layout import Constraints
        if constraints is None:
            constraints = Constraints()
        hw = self._hint_rect[2]
        hh = self._hint_rect[3]
        w = hw if hw > 0 else self._measure_text(self.text)
        h = hh if hh > 0 else (self._font_height() if self.text else 0)
        if hw == -1:
            w = constraints.max_w
        if hh == -1:
            h = constraints.max_h
        return (constraints.clamp_w(w), constraints.clamp_h(h))

    def render(self, renderer) -> None:
        if not self.visible or not self.text or self._factory is None:
            return
        # 文本或颜色变化时重建纹理
        if self._cached != (self.text, self.color):
            style = self._color_styles[self.color]
            surface = self.font.render_text(self.text, style=style)
            self._sprite = self._factory.from_surface(surface, free=True)
            self._cached = (self.text, self.color)
        x, y, w, h = self.abs_rect
        tw, th = self._sprite.size
        # 透明度：文字纹理 alpha 调制
        if self._render_opacity < 1.0:
            sdl2.SDL_SetTextureBlendMode(
                self._sprite.texture, sdl2.SDL_BLENDMODE_BLEND
            )
            sdl2.SDL_SetTextureAlphaMod(
                self._sprite.texture, int(255 * self._render_opacity)
            )
        # 注意：renderer.copy 必须显式传 dstrect，否则纹理会被拉伸到整个渲染目标
        renderer.copy(
            self._sprite,
            dstrect=(x, y + (h - th) // 2, tw, th),
        )
