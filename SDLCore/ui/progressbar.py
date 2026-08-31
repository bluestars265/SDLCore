# -*- coding: utf-8 -*-
"""ProgressBar：进度条控件（继承 Widget）。

- 数值管理：``min`` / ``max`` / ``value``，自动钳制；``min >= max`` 时自动修正。
- 渲染：背景矩形 + 按进度比从左侧填充 + 边框。
- 样式：颜色参数支持运行时修改（渲染每帧读取当前值，自动生效）。
- ``show_text`` 预留：``text_sprite`` 供后续集成百分比文字渲染。
"""

import sdl2

from SDLCore.resource import resources as default_resources
from SDLCore.ui.widget import Widget
from SDLCore.ui import apply_opacity


class ProgressBar(Widget):
    """横向进度条控件。"""

    def __init__(
        self,
        rect,
        min: float = 0.0,
        max: float = 100.0,
        value: float = 0.0,
        bg_color=(40, 40, 40, 255),
        fill_color=(0, 200, 80, 255),
        border_color=(80, 80, 80, 255),
        border_width: int = 1,
        show_text: bool = False,
        fill_image=None,
        indicator_image=None,
        factory=None,
        resources=None,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        super().__init__(rect, parent=parent, visible=visible, enabled=enabled)
        self.bg_color = tuple(bg_color)
        self.fill_color = tuple(fill_color)
        self.border_color = tuple(border_color)
        self.border_width = int(border_width)
        if self.border_width < 0:
            self.border_width = 0   # 注意：min/max 为参数名，勿用内置函数
        self.show_text = show_text

        self.min = float(min)
        self.max = float(max)
        if self.max <= self.min:
            self.max = self.min + 1.0   # 保证 min < max
        self.value = self._clamp(float(value))

        self.text_sprite = None         # 预留：show_text 为 True 时的文字纹理

        # 图片资源：填充纹理 / 前端标记（经全局 ResourceManager 缓存）
        self.resources = resources or default_resources
        self.fill_image = fill_image
        self.indicator_image = indicator_image
        self._factory = None
        self.fill_texture = None
        self.indicator_texture = None
        if factory is not None:
            self.set_factory(factory)
        elif self.resources.factory is not None:
            self.set_factory(self.resources.factory)

    # ---- 数值管理 ----

    def _clamp(self, v: float) -> float:
        return max(self.min, min(v, self.max))

    def set_value(self, val: float) -> None:
        """更新当前值（自动钳制在 [min, max]）。"""
        self.value = self._clamp(float(val))

    def set_range(self, min_val: float, max_val: float) -> None:
        """更新数值范围，并调整当前值以适应新范围。"""
        self.min = float(min_val)
        self.max = float(max_val)
        if self.max <= self.min:
            self.max = self.min + 1.0
        self.value = self._clamp(self.value)

    def get_progress(self) -> float:
        """返回 0.0 ~ 1.0 的进度比。"""
        return (self.value - self.min) / (self.max - self.min)

    # ---- 样式（运行时修改，渲染自动生效） ----

    def set_bg_color(self, color) -> None:
        self.bg_color = tuple(color)

    def set_fill_color(self, color) -> None:
        self.fill_color = tuple(color)

    def set_border_color(self, color) -> None:
        self.border_color = tuple(color)

    # ---- 图片资源 ----

    def _load_textures(self) -> None:
        """经资源管理器加载填充纹理与前端标记；失败时打印警告并回退。"""
        self.fill_texture = None
        self.indicator_texture = None
        if self._factory is None:
            if self.fill_image or self.indicator_image:
                print("警告: ProgressBar 传入了图片但未提供 factory，回退为纯色模式")
            return
        if self.fill_image:
            try:
                # 经资源管理器获取（缓存命中复用，避免重复加载）
                self.fill_texture = self.resources.get(self.fill_image)
                sdl2.SDL_SetTextureBlendMode(
                    self.fill_texture.texture, sdl2.SDL_BLENDMODE_BLEND
                )
            except Exception as exc:  # noqa: BLE001
                print(f"警告: 填充纹理加载失败 {self.fill_image}: {exc}")
                self.fill_texture = None
        if self.indicator_image:
            try:
                self.indicator_texture = self.resources.get(self.indicator_image)
                sdl2.SDL_SetTextureBlendMode(
                    self.indicator_texture.texture, sdl2.SDL_BLENDMODE_BLEND
                )
            except Exception as exc:  # noqa: BLE001
                print(f"警告: 指示器图片加载失败 {self.indicator_image}: {exc}")
                self.indicator_texture = None

    def set_factory(self, factory) -> None:
        """运行时设置渲染工厂（同时注册到资源管理器）并重新加载图片。"""
        self._factory = factory
        self.resources.set_factory(factory)
        self._load_textures()

    # ---- 渲染 ----

    def render(self, renderer) -> None:
        if not self.visible:
            return
        x, y, w, h = self.abs_rect
        op = self._render_opacity

        # 背景
        renderer.fill((x, y, w, h), apply_opacity(self.bg_color, op))

        # 填充（水平，从左侧开始，宽度 = 进度比 × 总宽）
        progress = self.get_progress()
        fill_w = int(w * progress)
        if fill_w > 0:
            if self.fill_texture is not None:
                if op < 1.0:
                    sdl2.SDL_SetTextureBlendMode(
                        self.fill_texture.texture, sdl2.SDL_BLENDMODE_BLEND
                    )
                    sdl2.SDL_SetTextureAlphaMod(
                        self.fill_texture.texture, int(255 * op)
                    )
                # 纹理自动拉伸填满填充矩形（dstrect 缺省会拉伸到整个渲染目标，故必须显式传）
                renderer.copy(self.fill_texture, dstrect=(x, y, fill_w, h))
            else:
                renderer.fill((x, y, fill_w, h),
                              apply_opacity(self.fill_color, op))

        # 前端标记：中心对齐到填充末端，随进度移动（保持图片原始宽高比）
        if self.indicator_texture is not None:
            iw, ih = self.indicator_texture.size
            if op < 1.0:
                sdl2.SDL_SetTextureBlendMode(
                    self.indicator_texture.texture, sdl2.SDL_BLENDMODE_BLEND
                )
                sdl2.SDL_SetTextureAlphaMod(
                    self.indicator_texture.texture, int(255 * op)
                )
            ind_x = x + int((w - iw) * progress)
            ind_y = y + (h - ih) // 2
            renderer.copy(self.indicator_texture, dstrect=(ind_x, ind_y, iw, ih))

        # 边框（由外向内逐层绘制）
        for i in range(self.border_width):
            renderer.draw_rect(
                (x + i, y + i, w - 2 * i, h - 2 * i),
                apply_opacity(self.border_color, op),
            )

        # show_text 预留：后续在此渲染 self.text_sprite（百分比文字）
