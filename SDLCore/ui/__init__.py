# -*- coding: utf-8 -*-
"""SDLCore.ui：通用 GUI 控件库（不含任何游戏业务逻辑）。"""

import ctypes
import os

import sdl2

# 项目根目录（本文件位于 II/SDLCore/ui/__init__.py）
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
# 字体资源目录：II/resource/fonts/
FONTS_DIR = os.path.join(_PROJECT_ROOT, "resource", "fonts")

# 系统字体回退候选（Windows）
_SYSTEM_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\msyh.ttc",    # 微软雅黑
    r"C:\Windows\Fonts\simhei.ttf",  # 黑体（SimHei）
    r"C:\Windows\Fonts\simsun.ttc",  # 宋体
)


def apply_opacity(color, opacity: float):
    """按透明度调制颜色 alpha；opacity >= 1 或颜色无 alpha 时原样返回。"""
    if opacity >= 1.0 or len(color) < 4:
        return color
    c = list(color)
    c[3] = int(color[3] * max(0.0, min(1.0, opacity)))
    return tuple(c)


def enable_alpha_blend(renderer) -> None:
    """为渲染器启用 alpha 混合，使半透明颜色的绘制生效。"""
    sdl2.SDL_SetRenderDrawBlendMode(
        renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND
    )


def set_render_clip(renderer, rect) -> None:
    """设置渲染裁剪矩形；rect 为 None 表示恢复无裁剪。

    兼容 BatchedRenderer（通过 set_clip_rect 通知合批器）与原生 Renderer。
    """
    setter = getattr(renderer, "set_clip_rect", None)
    if setter is not None:
        setter(rect)
    elif rect is None:
        sdl2.SDL_RenderSetClipRect(renderer.sdlrenderer, None)
    else:
        sdl2.SDL_RenderSetClipRect(renderer.sdlrenderer, ctypes.byref(rect))


def find_font() -> str | None:
    """查找可用字体：优先递归扫描项目 resource/fonts/，回退到系统字体。"""
    if os.path.isdir(FONTS_DIR):
        for root, dirs, files in os.walk(FONTS_DIR):
            # 跳过 __MACOSX 等系统残留目录
            dirs[:] = [d for d in dirs if not d.startswith("__")]
            for name in sorted(files):
                if name.lower().endswith((".ttf", ".ttc", ".otf")):
                    return os.path.join(root, name)
    for path in _SYSTEM_FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None

