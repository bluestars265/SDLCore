# -*- coding: utf-8 -*-
"""ImageButton：带三态图片的图片按钮控件（继承自 Button，原 Button 保留）。

- NORMAL（常态）/ HOVER（悬停）/ PRESSED（按下）三种状态各自对应一张图片。
- 图片会被缩放（拉伸）到按钮矩形大小。
- 可显示文字（可选，居中；``text`` 为空则只显示图片）。
- 某状态未提供图片时，该状态回退为 Button 的颜色渲染。
"""

import sdl2

from SDLCore.resource import resources as default_resources
from SDLCore.ui.button import Button, ButtonState
from SDLCore.ui.label import Label
from SDLCore.ui.layout import Constraints


class ImageButton(Button):
    """使用三态图片的按钮控件（图片经全局 ResourceManager 缓存）。"""

    def __init__(
        self,
        rect,
        image_normal=None,
        image_hover=None,
        image_pressed=None,
        text: str = "",
        text_color=(255, 255, 255, 255),
        callback=None,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
        factory=None,
        resources=None,
    ) -> None:
        super().__init__(
            rect,
            text=text,
            callback=callback,
            parent=parent,
            visible=visible,
            enabled=enabled,
        )
        self.resources = resources or default_resources
        self.image_normal = image_normal
        self.image_hover = image_hover
        self.image_pressed = image_pressed
        self.text_color = tuple(text_color)
        self._factory = None
        self._sprites = {}  # ButtonState -> TextureSprite
        self._text_label = None  # 可选文字（text 非空且 factory 时创建）
        if factory is not None:
            self.set_factory(factory)
        elif self.resources.factory is not None:
            self.set_factory(self.resources.factory)

    def set_factory(self, factory) -> None:
        """设置渲染工厂（同时注册到资源管理器）并加载三态图片。"""
        self._factory = factory
        self.resources.set_factory(factory)
        self._load_sprites()
        self._ensure_text_label()

    def _ensure_text_label(self) -> None:
        """text 非空且 factory 可用时创建文字 Label（居中显示）。"""
        if self.text and self._text_label is None and self._factory is not None:
            self._text_label = Label(
                (0, 0, 0, 0), text=self.text, color=self.text_color,
                font_size="14px", factory=self._factory,
            )

    def _load_sprites(self) -> None:
        self._sprites = {}
        images = {
            ButtonState.NORMAL: self.image_normal,
            ButtonState.HOVER: self.image_hover,
            ButtonState.PRESSED: self.image_pressed,
        }
        for state, path in images.items():
            if not path:
                continue
            try:
                # 经资源管理器获取（缓存命中复用，避免重复加载）
                sprite = self.resources.get(path)
                # 启用 alpha 混合，使 PNG 透明背景正确显示
                sdl2.SDL_SetTextureBlendMode(sprite.texture, sdl2.SDL_BLENDMODE_BLEND)
                self._sprites[state] = sprite
            except Exception as exc:  # noqa: BLE001
                print(f"警告: 图片加载失败 {path}: {exc}")

    def measure(self, constraints=None):
        """首选尺寸：优先使用图片原始尺寸。"""
        from SDLCore.ui.layout import Constraints
        if constraints is None:
            constraints = Constraints()
        sprite = self._sprites.get(ButtonState.NORMAL)
        if sprite is not None:
            return (constraints.clamp_w(sprite.size[0]),
                    constraints.clamp_h(sprite.size[1]))
        return super().measure(constraints)

    def render(self, renderer) -> None:
        if not self.visible:
            return
        sprite = self._sprites.get(self.state)
        if sprite is not None:
            x, y, w, h = self.abs_rect
            if self._render_opacity < 1.0:
                sdl2.SDL_SetTextureBlendMode(
                    sprite.texture, sdl2.SDL_BLENDMODE_BLEND
                )
                sdl2.SDL_SetTextureAlphaMod(
                    sprite.texture, int(255 * self._render_opacity)
                )
            # 图片缩放为按钮大小（dstrect 缺省会拉伸到整个渲染目标，故必须显式传）
            renderer.copy(sprite, dstrect=(x, y, w, h))
        else:
            # 该状态未配置图片：回退为 Button 的颜色渲染
            super().render(renderer)
        # 可选文字：水平垂直居中显示（透明度传播）
        if self._text_label is not None:
            saved = self._text_label._render_opacity
            self._text_label._render_opacity = (
                self._render_opacity * self._text_label.opacity
            )
            self._text_label.set_text(self.text)
            tw, th = self._text_label.measure(Constraints())
            x, y, w, h = self.abs_rect
            self._text_label.abs_rect = (
                x + (w - tw) // 2, y + (h - th) // 2, tw, th,
            )
            self._text_label.render(renderer)
            self._text_label._render_opacity = saved
