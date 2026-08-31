# -*- coding: utf-8 -*-
"""ScrollPanel：滚动面板（继承 Panel）。

- 内部维护一个 ``content`` 子面板，所有 ``add_child`` 的控件都挂载到 ``content`` 上。
- 支持垂直与水平滚动：滚轮（wheel.y 垂直、wheel.x 水平）或**拖拽滚动条滑块**。
- 滚动条滑块可使用图片（``thumb_image`` / ``thumb_image_h``），否则用纯色方块。
- 渲染时裁剪到视口，超出部分不可见。
- ``content_size`` 为 ``None`` 时，根据子控件占用范围自动计算内容大小。
"""

import ctypes

import sdl2

from SDLCore.resource import resources as default_resources
from SDLCore.ui.panel import Panel
from SDLCore.ui.widget import Widget
from SDLCore.ui import enable_alpha_blend, set_render_clip, apply_opacity


class ScrollPanel(Panel):
    """带视口裁剪、滚轮滚动与可拖拽滚动条的面板容器。"""

    THUMB_MIN = 20  # 滑块最小尺寸（px）

    def __init__(
        self,
        rect,
        content_size=None,
        scroll_speed: float = 30.0,
        show_v_scrollbar: bool = True,
        show_h_scrollbar: bool = True,
        scrollbar_width: int = 8,
        track_color=(80, 80, 80, 120),
        thumb_color=(160, 160, 160, 220),
        thumb_image=None,
        thumb_image_h=None,
        factory=None,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        super().__init__(rect, parent=parent, visible=visible, enabled=enabled)
        self.content_size = content_size      # None 表示自动适应子控件
        self.scroll_speed = scroll_speed      # 滚轮每格滚动像素数
        self.show_v_scrollbar = show_v_scrollbar  # 垂直滚动条
        self.show_h_scrollbar = show_h_scrollbar  # 水平滚动条
        self.scrollbar_width = int(scrollbar_width)
        self.track_color = tuple(track_color)
        self.thumb_color = tuple(thumb_color)
        self.thumb_image = thumb_image        # 垂直滑块图片（可选）
        self.thumb_image_h = thumb_image_h    # 水平滑块图片（可选）
        self.scroll_x = 0.0                   # 横向滚动偏移（px）
        self.scroll_y = 0.0                   # 纵向滚动偏移（px）

        # 滑块拖拽状态
        self._drag_v = False
        self._drag_h = False
        self._drag_offset = 0

        if content_size is not None:
            cw, ch = int(content_size[0]), int(content_size[1])
        else:
            cw = ch = 0
        self._content_w = cw                  # 内容逻辑宽
        self._content_h = ch                  # 内容逻辑高

        # 滑块纹理（经全局 ResourceManager 缓存）
        self.resources = default_resources
        self._v_thumb_tex = None
        self._h_thumb_tex = None
        if factory is not None:
            self.resources.set_factory(factory)
            self._load_thumb_images()

        # 内容面板：作为本控件的子控件，实际控件都挂到它上面
        self.content = Panel((0, 0, cw, ch), color=(0, 0, 0, 0))
        super().add_child(self.content)

    def _load_thumb_images(self) -> None:
        """加载滚动条滑块图片（失败回退为纯色）。"""
        self._v_thumb_tex = None
        self._h_thumb_tex = None
        try:
            if self.thumb_image:
                self._v_thumb_tex = self.resources.get(self.thumb_image)
                sdl2.SDL_SetTextureBlendMode(
                    self._v_thumb_tex.texture, sdl2.SDL_BLENDMODE_BLEND
                )
            if self.thumb_image_h:
                self._h_thumb_tex = self.resources.get(self.thumb_image_h)
                sdl2.SDL_SetTextureBlendMode(
                    self._h_thumb_tex.texture, sdl2.SDL_BLENDMODE_BLEND
                )
            elif self._v_thumb_tex is not None:
                self._h_thumb_tex = self._v_thumb_tex  # 水平滑块共用垂直滑块图
        except Exception as exc:  # noqa: BLE001
            print(f"警告: 滚动条滑块图片加载失败: {exc}")

    # ---- 内容容器 ----

    def add_child(self, widget) -> Widget:
        """重定向：挂载到内部 content 面板，并自动刷新内容尺寸。"""
        self.content.add_child(widget)
        self._auto_size_content()
        return widget

    def remove_child(self, widget) -> None:
        """重定向：从内部 content 面板移除，并自动刷新内容尺寸。"""
        self.content.remove_child(widget)
        self._auto_size_content()

    def get_content(self) -> Panel:
        """返回内部 content 面板引用。"""
        return self.content

    def _auto_size_content(self) -> None:
        """content_size 为 None 时，按子控件占用范围自动计算内容尺寸。"""
        if self.content_size is not None:
            return
        w = h = 0
        for child in self.content.children:
            if not child.visible:
                continue
            cx, cy, cw, ch = child.rect
            w = max(w, cx + cw)
            h = max(h, cy + ch)
        self._content_w = w
        self._content_h = h

    # ---- 滚动 ----

    def scroll_to(self, x, y) -> None:
        """滚动到指定偏移（自动钳制到有效范围）。"""
        max_x = max(0.0, float(self._content_w - self.rect[2]))
        max_y = max(0.0, float(self._content_h - self.rect[3]))
        self.scroll_x = max(0.0, min(float(x), max_x))
        self.scroll_y = max(0.0, min(float(y), max_y))

    def _clamp_scroll(self) -> None:
        """将当前滚动偏移钳制到有效范围。"""
        self.scroll_to(self.scroll_x, self.scroll_y)

    def _sync_content_offset(self) -> None:
        """把滚动偏移写入 content 相对坐标，并刷新全子树绝对坐标。"""
        self._clamp_scroll()
        x, y, _w, _h = self.abs_rect
        self.content.rect = (
            -self.scroll_x, -self.scroll_y, self._content_w, self._content_h,
        )
        self.content.update_abs_position(x, y)

    # ---- 滚动条几何 ----

    def _v_thumb_rect(self):
        """垂直滑块矩形（无滚动空间或隐藏时返回 None）。"""
        if not self.show_v_scrollbar or self._content_h <= self.rect[3]:
            return None
        x, y, w, h = self.abs_rect
        max_scroll = max(1, self._content_h - self.rect[3])
        thumb_h = max(self.THUMB_MIN, int(h * h / self._content_h))
        ratio = max(0.0, min(1.0, self.scroll_y / max_scroll))
        return (x + w - self.scrollbar_width,
                y + int((h - thumb_h) * ratio), self.scrollbar_width, thumb_h)

    def _h_thumb_rect(self):
        """水平滑块矩形（无滚动空间或隐藏时返回 None）。"""
        if not self.show_h_scrollbar or self._content_w <= self.rect[2]:
            return None
        x, y, w, h = self.abs_rect
        max_scroll = max(1, self._content_w - self.rect[2])
        thumb_w = max(self.THUMB_MIN, int(w * w / self._content_w))
        ratio = max(0.0, min(1.0, self.scroll_x / max_scroll))
        return (x + int((w - thumb_w) * ratio),
                y + h - self.scrollbar_width, thumb_w, self.scrollbar_width)

    def _hit_v_thumb(self, px: int, py: int) -> bool:
        r = self._v_thumb_rect()
        if r is None:
            return False
        rx, ry, rw, rh = r
        return rx <= px < rx + rw and ry <= py < ry + rh

    def _hit_h_thumb(self, px: int, py: int) -> bool:
        r = self._h_thumb_rect()
        if r is None:
            return False
        rx, ry, rw, rh = r
        return rx <= px < rx + rw and ry <= py < ry + rh

    def _drag_v_thumb(self, my: int) -> None:
        r = self._v_thumb_rect()
        if r is None:
            return
        x, y, w, h = self.abs_rect
        _rx, _ry, _rw, rh = r
        track = h - rh
        if track <= 0:
            return
        max_scroll = max(0, self._content_h - self.rect[3])
        ratio = (my - y - self._drag_offset) / track
        self.scroll_y = max(0.0, min(max_scroll, ratio * max_scroll))

    def _drag_h_thumb(self, mx: int) -> None:
        r = self._h_thumb_rect()
        if r is None:
            return
        x, y, w, h = self.abs_rect
        _rx, _ry, rw, _rh = r
        track = w - rw
        if track <= 0:
            return
        max_scroll = max(0, self._content_w - self.rect[2])
        ratio = (mx - x - self._drag_offset) / track
        self.scroll_x = max(0.0, min(max_scroll, ratio * max_scroll))

    # ---- 事件 ----

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False

        # 滚动条滑块拖拽
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if event.button.button == sdl2.SDL_BUTTON_LEFT:
                if self._hit_v_thumb(event.button.x, event.button.y):
                    self._drag_v = True
                    _rx, ry, _rw, _rh = self._v_thumb_rect()
                    self._drag_offset = event.button.y - ry
                    return True
                if self._hit_h_thumb(event.button.x, event.button.y):
                    self._drag_h = True
                    _rx, _ry, _rw, _rh = self._h_thumb_rect()
                    self._drag_offset = event.button.x - _rx
                    return True
        if event.type == sdl2.SDL_MOUSEMOTION:
            if self._drag_v:
                self._drag_v_thumb(event.motion.y)
                return True
            if self._drag_h:
                self._drag_h_thumb(event.motion.x)
                return True
            # 非拖拽：分发给子控件（含 content 上的实际控件）
            return super().handle_event(event)
        if event.type == sdl2.SDL_MOUSEBUTTONUP:
            if event.button.button == sdl2.SDL_BUTTON_LEFT and (
                self._drag_v or self._drag_h
            ):
                self._drag_v = False
                self._drag_h = False
                return True

        # 其余事件分发给子控件；未消费则处理滚轮（含水平 wheel.x）
        consumed = super().handle_event(event)
        if not consumed and event.type == sdl2.SDL_MOUSEWHEEL:
            mx = ctypes.c_int(0)
            my = ctypes.c_int(0)
            sdl2.SDL_GetMouseState(ctypes.byref(mx), ctypes.byref(my))
            if self._contains(mx.value, my.value):
                dy = event.wheel.y
                dx = event.wheel.x
                if event.wheel.direction == sdl2.SDL_MOUSEWHEEL_FLIPPED:
                    dy = -dy
                    dx = -dx
                self.scroll_y -= dy * self.scroll_speed
                self.scroll_x -= dx * self.scroll_speed
                self._clamp_scroll()
                return True
        return consumed

    # ---- 渲染 ----

    def render(self, renderer) -> None:
        if not self.visible:
            return
        x, y, w, h = self.abs_rect
        # 背景
        enable_alpha_blend(renderer)
        renderer.fill(
            (x, y, w, h), apply_opacity(self.color, self._render_opacity)
        )
        # 同步滚动偏移，并将渲染裁剪到视口
        self._sync_content_offset()
        clip = sdl2.SDL_Rect(x, y, w, h)
        set_render_clip(renderer, clip)
        # 渲染内容并传播透明度
        saved = self.content._render_opacity
        self.content._render_opacity = self._render_opacity * self.content.opacity
        self.content.render(renderer)
        self.content._render_opacity = saved
        set_render_clip(renderer, None)
        # 滚动条（轨道 + 滑块，绘制在内容之上）
        self._draw_scrollbars(renderer)

    def _draw_scrollbars(self, renderer) -> None:
        x, y, w, h = self.abs_rect
        sw = self.scrollbar_width
        track = apply_opacity(self.track_color, self._render_opacity)
        # 垂直滚动条
        v = self._v_thumb_rect()
        if v is not None:
            enable_alpha_blend(renderer)
            renderer.fill((x + w - sw, y, sw, h), track)
            self._draw_thumb(renderer, v, self._v_thumb_tex)
        # 水平滚动条
        hh = self._h_thumb_rect()
        if hh is not None:
            enable_alpha_blend(renderer)
            renderer.fill((x, y + h - sw, w, sw), track)
            self._draw_thumb(renderer, hh, self._h_thumb_tex)

    def _draw_thumb(self, renderer, rect, tex) -> None:
        if tex is not None:
            if self._render_opacity < 1.0:
                sdl2.SDL_SetTextureAlphaMod(
                    tex.texture, int(255 * self._render_opacity)
                )
            renderer.copy(tex, dstrect=rect)  # 图片滑块（拉伸到滑块矩形）
        else:
            renderer.fill(rect, apply_opacity(  # 纯色方块滑块
                self.thumb_color, self._render_opacity
            ))
