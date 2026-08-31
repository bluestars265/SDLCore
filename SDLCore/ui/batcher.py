# -*- coding: utf-8 -*-
"""BatchedRenderer：渲染合批器（矩形合批）。

- 包装 ``sdl2.ext.Renderer``，把**不透明纯色矩形**（fill / draw_rect）收集为绘制命令，
  相邻同色矩形用 ``SDL_RenderFillRects`` / ``SDL_RenderDrawRects`` **一次提交多个**，
  显著减少 Draw Call（适合大量按钮 / 进度条 / 列表项等）。
- 半透明矩形与**裁剪区域内**的矩形保持逐次绘制，保证 alpha 混合与裁剪正确。
- ``copy``（纹理）在提交前 flush 已收集命令，保证 z 顺序。
- 裁剪感知：通过 ``set_clip_rect`` 钩子（见 ``SDLCore.ui.set_render_clip``）告知裁剪状态。
"""

import ctypes

import sdl2


class BatchedRenderer:
    """代理 renderer：合并不透明矩形绘制。"""

    def __init__(self, renderer):
        self._r = renderer
        self._cmds = []       # [(kind, color, rect)]  kind: "fill" / "draw"
        self._clipped = False # 是否处于裁剪状态（裁剪内矩形不合批）

    # ---- 收集 / 转发 ----

    def fill(self, rect, color):
        if self._clipped or (len(color) >= 4 and color[3] != 255):
            self._flush()
            self._r.fill(rect, color)
        else:
            self._cmds.append(("fill", tuple(color), tuple(rect)))

    def draw_rect(self, rect, color):
        if self._clipped or (len(color) >= 4 and color[3] != 255):
            self._flush()
            self._r.draw_rect(rect, color)
        else:
            self._cmds.append(("draw", tuple(color), tuple(rect)))

    def copy(self, *args, **kwargs):
        # 纹理复制必须在已收集命令之前绘制（保证 z 顺序）
        self._flush()
        self._r.copy(*args, **kwargs)

    def set_clip_rect(self, rect):
        """设置渲染裁剪（通知合批器：裁剪内矩形不合批）。rect 为 None 表示恢复。"""
        self._flush()
        self._clipped = rect is not None
        if rect is None:
            sdl2.SDL_RenderSetClipRect(self._r.sdlrenderer, None)
        else:
            sdl2.SDL_RenderSetClipRect(self._r.sdlrenderer, ctypes.byref(rect))

    def flush(self):
        self._flush()

    # ---- 内部 ----

    def _flush(self):
        if not self._cmds:
            return
        # 按 (kind, color) 全量分组（同色矩形全部合并），按首次出现顺序绘制
        groups = {}     # (kind, color) -> [rect, ...]
        order = []      # 首次出现的 (kind, color)
        seq = {}        # (kind, color) -> 首次出现序号
        for idx, (kind, color, rect) in enumerate(self._cmds):
            key = (kind, color)
            if key not in groups:
                groups[key] = []
                order.append(key)
                seq[key] = idx
            groups[key].append(rect)
        for key in sorted(order, key=lambda k: seq[k]):
            kind, color = key
            rects = groups[key]
            sdl2.SDL_SetRenderDrawColor(self._r.sdlrenderer, *color)
            arr = (sdl2.SDL_Rect * len(rects))(
                *[sdl2.SDL_Rect(*r) for r in rects]
            )
            if kind == "fill":
                sdl2.SDL_RenderFillRects(self._r.sdlrenderer, arr, len(rects))
            else:
                sdl2.SDL_RenderDrawRects(self._r.sdlrenderer, arr, len(rects))
        self._cmds = []

    # ---- 透传 ----

    @property
    def sdlrenderer(self):
        return self._r.sdlrenderer

    def __getattr__(self, name):
        return getattr(self._r, name)
