# -*- coding: utf-8 -*-
"""Image：图片显示控件（通用引擎层，与具体游戏无关）。

- 显示图片纹理（PNG / SVG 等，经 ResourceManager 加载或直接传入纹理）。
- **保持宽高比缩放并居中，不填充背景**（适配 logo / 图标等素材）。
"""

import sdl2

from SDLCore.resource import resources
from SDLCore.ui.widget import Widget


class Image(Widget):
    """纯图片控件：保持宽高比居中显示，不拉伸填充。"""

    def __init__(
        self,
        rect,
        path=None,
        texture=None,
        id=None,
        layer: int = 0,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        super().__init__(
            rect, id=id, layer=layer, parent=parent,
            visible=visible, enabled=enabled,
        )
        self._texture = None
        if texture is not None:
            self._texture = texture
        elif path:
            try:
                self._texture = resources.get(path)
            except Exception as exc:  # noqa: BLE001
                print(f"警告: Image 加载失败 {path}: {exc}")

    @property
    def texture(self):
        return self._texture

    def set_texture(self, texture) -> None:
        """运行时更换纹理。"""
        self._texture = texture
        self.mark_dirty()

    def render(self, renderer) -> None:
        if not self.visible or self._texture is None:
            return
        sdl2.SDL_SetTextureBlendMode(
            self._texture.texture, sdl2.SDL_BLENDMODE_BLEND
        )
        x, y, w, h = self.abs_rect
        iw, ih = self._texture.size
        if iw <= 0 or ih <= 0:
            return
        scale = min(w / iw, h / ih)
        dw = max(1, int(iw * scale))
        dh = max(1, int(ih * scale))
        # 注意：renderer.copy 必须显式传 dstrect，否则纹理会被拉伸到整个渲染目标
        renderer.copy(self._texture,
                      dstrect=(x + (w - dw) // 2, y + (h - dh) // 2, dw, dh))
