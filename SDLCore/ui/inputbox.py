# -*- coding: utf-8 -*-
"""InputBox：支持系统 IME（中文/日文输入法）的文本输入框控件。

交互流程：
- 鼠标左键点击框内激活（sdl2.SDL_StartTextInput 启用 IME），点击框外失焦。
- ``SDL_TEXTINPUT`` 事件：输入法直接上屏的 UTF-8 文本插入光标处。
- ``SDL_TEXTEDITING`` 事件：输入法未上屏的组合文本（如拼音）暂存并显示。
- ``SDL_KEYDOWN``：退格/删除/左右移动光标/回车提交，支持 Home/End 跳转与 Shift 扩展选区。
- 标准编辑：Ctrl+A 全选、Ctrl+C/X/V 复制/剪切/粘贴（系统剪贴板）、鼠标拖拽选择。

渲染：白色背景 + 状态边框（未聚焦灰/聚焦蓝）+ 选区高亮 + 文本纹理 + 闪烁光标 + 灰色组合文本。
"""

import ctypes

import sdl2
import sdl2.ext
from sdl2.ext.ttf import FontTTF

from SDLCore.ui import enable_alpha_blend, find_font, set_render_clip, apply_opacity
from SDLCore.ui.widget import Widget


class InputBox(Widget):
    """可调用系统输入法（IME）的文本输入框。"""

    COLOR_BG = (255, 255, 255, 255)
    COLOR_NORMAL = (120, 120, 120, 255)
    COLOR_ACTIVE = (30, 120, 200, 255)
    COLOR_TEXT = (0, 0, 0, 255)
    COLOR_COMPOSING = (130, 130, 130, 255)
    COLOR_CARET = (0, 0, 0, 255)
    COLOR_SELECTION = (0, 120, 215, 100)      # 选区高亮（半透明蓝）
    CARET_WIDTH = 2
    CARET_BLINK_INTERVAL = 0.5        # 光标闪烁半周期（秒）
    TEXT_PADDING = 5                  # 文本距输入框左缘间距（px）

    def __init__(
        self,
        rect,
        font_path=None,
        font_size="18px",
        on_submit=None,
        parent=None,
        visible: bool = True,
        enabled: bool = True,
        factory=None,
    ) -> None:
        super().__init__(rect, parent=parent, visible=visible, enabled=enabled)
        self.text = ""                 # 当前输入内容
        self.active = False            # 是否持有输入焦点
        self.cursor_pos = 0            # 光标在文本中的索引
        self.cursor_visible = False    # 光标闪烁开关
        self.cursor_timer = 0.0        # 闪烁计时累计（秒）
        self.composing_text = ""       # IME 未上屏的组合文本（拼音等）
        self.on_submit = on_submit     # 回车提交回调
        self.sel_start = -1            # 选区锚点索引（-1 表示无选区）
        self._dragging = False         # 是否正在拖拽选择

        # 字体：优先项目 resource/fonts/，回退系统字体，保证中文渲染
        font_path = font_path or find_font()
        if font_path is None:
            raise RuntimeError("未找到可用字体（resource/fonts/ 或系统字体）")
        self.font = FontTTF(font_path, font_size, self.COLOR_TEXT)
        self.font.add_style("composing", font_size, self.COLOR_COMPOSING)

        self._factory = None
        self._text_sprite = None
        self._cached_text = None
        self._composing_sprite = None
        self._cached_composing = None
        self._scroll_offset = 0  # 横向滚动偏移（px），文本过长时保证光标可见
        if factory is not None:
            self.set_factory(factory)

    # ---- 配置接口 ----

    def set_text(self, text: str) -> None:
        """设置输入框内容，并将光标移动到末尾。"""
        self.text = text
        self.cursor_pos = len(text)
        self.sel_start = -1

    # ---- 焦点管理 ----

    def _get_manager(self):
        """沿父链向上查找所属 UIManager。"""
        node = self
        while node is not None:
            manager = getattr(node, "_manager", None)
            if manager is not None:
                return manager
            node = getattr(node, "parent", None)
        return None

    def _set_active(self, active: bool) -> None:
        if self.active == active:
            return
        self.active = active
        manager = self._get_manager()
        if active:
            sdl2.SDL_StartTextInput()       # 启用系统 IME
            # 确保系统 IME 原生 UI 开启（正确 hint 名；主要已在窗口创建前设置）
            sdl2.SDL_SetHint(b"SDL_IME_SHOW_UI", b"1")
            self.cursor_timer = 0.0
            self.cursor_visible = True
            self._update_ime_rect()         # 定位候选窗口到光标处
            if manager is not None:
                manager.set_focus(self)
        else:
            sdl2.SDL_StopTextInput()        # 关闭系统 IME
            self.composing_text = ""
            self.sel_start = -1
            self._dragging = False
            if manager is not None and manager.focused_widget is self:
                manager.set_focus(None)

    def _update_ime_rect(self) -> None:
        """将系统 IME 候选窗口/组合条定位到输入框光标处（跟随滚动与窗口缩放）。

        SDL 在 Windows 上依赖 ``SDL_SetTextInputRect`` 决定 IME UI 的显示位置；
        若不设置，输入法不会显示候选词与组合条（但 ``SDL_TEXTINPUT`` 事件仍正常，
        因此数字键选词依旧有效）。
        """
        if not self.active:
            return
        x, y, w, h = self.abs_rect
        caret_x = (
            self.TEXT_PADDING
            + self._measure_text(self.text[:self.cursor_pos])
            - self._scroll_offset
        )
        caret_x = max(0, caret_x)
        rect = sdl2.SDL_Rect(x + caret_x, y, 2, h)
        sdl2.SDL_SetTextInputRect(ctypes.byref(rect))

    # ---- 文本编辑 ----

    def _insert_text(self, text: str) -> None:
        """在光标处插入文本；存在选区时先替换选区。"""
        if not text:
            return
        if self._has_selection():
            self._delete_selection()
        self.text = self.text[:self.cursor_pos] + text + self.text[self.cursor_pos:]
        self.cursor_pos += len(text)

    def _submit(self) -> None:
        self.composing_text = ""
        if self.on_submit is not None:
            self.on_submit(self.text)

    # ---- 选区 ----

    def _has_selection(self) -> bool:
        return self.sel_start is not None and self.sel_start >= 0

    def _selection_range(self):
        """返回 (sel_begin, sel_end)；无选区返回 None。"""
        if not self._has_selection():
            return None
        return (
            min(self.sel_start, self.cursor_pos),
            max(self.sel_start, self.cursor_pos),
        )

    def _selected_text(self) -> str:
        r = self._selection_range()
        return self.text[r[0]:r[1]] if r is not None else ""

    def _delete_selection(self) -> str:
        """删除选区并返回被删除文本；无选区返回空串。"""
        r = self._selection_range()
        if r is None:
            return ""
        begin, end = r
        deleted = self.text[begin:end]
        self.text = self.text[:begin] + self.text[end:]
        self.cursor_pos = begin
        self.sel_start = -1
        return deleted

    # ---- 剪贴板（系统剪贴板） ----

    def _copy(self) -> None:
        if self._has_selection():
            sdl2.SDL_SetClipboardText(self._selected_text().encode("utf-8"))

    def _cut(self) -> None:
        if self._has_selection():
            sdl2.SDL_SetClipboardText(self._selected_text().encode("utf-8"))
            self._delete_selection()

    def _paste(self) -> None:
        buf = sdl2.SDL_GetClipboardText()
        if buf:
            self._insert_text(buf.decode("utf-8", errors="replace"))

    # ---- 鼠标定位 ----

    def _index_at_x(self, px: int) -> int:
        """根据绝对 x 坐标计算文本索引（二分查找）。"""
        x, _y, _w, _h = self.abs_rect
        tx = px - (x + self.TEXT_PADDING - self._scroll_offset)
        if tx <= 0:
            return 0
        lo, hi = 0, len(self.text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._measure_text(self.text[:mid]) <= tx:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def _handle_key(self, sym, mod) -> bool:
        ctrl = bool(mod & sdl2.KMOD_CTRL)
        shift = bool(mod & sdl2.KMOD_SHIFT)

        # IME 组合期间：退格撤销组合字符，回车直接提交
        if self.composing_text:
            if sym == sdl2.SDLK_BACKSPACE:
                self.composing_text = self.composing_text[:-1]
            elif sym in (sdl2.SDLK_RETURN, sdl2.SDLK_KP_ENTER):
                self._submit()
            return True

        # Ctrl 组合键：全选 / 复制 / 剪切 / 粘贴
        if ctrl:
            if sym == sdl2.SDLK_a:
                self.sel_start = 0
                self.cursor_pos = len(self.text)
                return True
            if sym == sdl2.SDLK_c:
                self._copy()
                return True
            if sym == sdl2.SDLK_x:
                self._cut()
                return True
            if sym == sdl2.SDLK_v:
                self._paste()
                return True

        if sym == sdl2.SDLK_BACKSPACE:
            if self._has_selection():
                self._delete_selection()
            elif self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
            return True
        if sym == sdl2.SDLK_DELETE:
            if self._has_selection():
                self._delete_selection()
            elif self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
            return True
        if sym == sdl2.SDLK_LEFT:
            if shift:  # Shift+← 扩展选区
                if not self._has_selection():
                    self.sel_start = self.cursor_pos
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            elif self._has_selection():  # 无 Shift：折叠到选区左端
                self.cursor_pos = min(self.sel_start, self.cursor_pos)
                self.sel_start = -1
            elif self.cursor_pos > 0:
                self.cursor_pos -= 1
            return True
        if sym == sdl2.SDLK_RIGHT:
            if shift:
                if not self._has_selection():
                    self.sel_start = self.cursor_pos
                if self.cursor_pos < len(self.text):
                    self.cursor_pos += 1
            elif self._has_selection():
                self.cursor_pos = max(self.sel_start, self.cursor_pos)
                self.sel_start = -1
            elif self.cursor_pos < len(self.text):
                self.cursor_pos += 1
            return True
        if sym == sdl2.SDLK_HOME:
            if shift:
                if not self._has_selection():
                    self.sel_start = self.cursor_pos
                self.cursor_pos = 0
            else:
                self.cursor_pos = 0
                self.sel_start = -1
            return True
        if sym == sdl2.SDLK_END:
            if shift:
                if not self._has_selection():
                    self.sel_start = self.cursor_pos
                self.cursor_pos = len(self.text)
            else:
                self.cursor_pos = len(self.text)
                self.sel_start = -1
            return True
        if sym in (sdl2.SDLK_RETURN, sdl2.SDLK_KP_ENTER):
            self._submit()
            return True
        return False

    # ---- 事件处理 ----

    def handle_event(self, event) -> bool:
        if not self.visible or not self.enabled:
            return False
        if event.type == sdl2.SDL_MOUSEMOTION:
            self._update_hover(event.motion.x, event.motion.y)
            if self._dragging:  # 拖拽选择
                self.cursor_pos = self._index_at_x(event.motion.x)
                self._update_ime_rect()
                return True
            return False
        if event.type == sdl2.SDL_MOUSEBUTTONDOWN:
            if event.button.button == sdl2.SDL_BUTTON_LEFT:
                inside = self._contains(event.button.x, event.button.y)
                self._set_active(inside)
                if inside:
                    # 设置光标 + 选区锚点，开始拖拽选择
                    idx = self._index_at_x(event.button.x)
                    self.cursor_pos = idx
                    self.sel_start = idx
                    self._dragging = True
                    self._update_ime_rect()
                    return True
            return False
        if event.type == sdl2.SDL_MOUSEBUTTONUP:
            if event.button.button == sdl2.SDL_BUTTON_LEFT and self._dragging:
                self._dragging = False
                return True
            return False
        if event.type == sdl2.SDL_TEXTINPUT:
            if self.active:
                self.composing_text = ""
                self._insert_text(event.text.text.decode("utf-8", errors="replace"))
                return True
            return False
        if event.type == sdl2.SDL_TEXTEDITING:
            if self.active:
                self.composing_text = event.edit.text.decode("utf-8", errors="replace")
                return True
            return False
        if event.type == sdl2.SDL_KEYDOWN:
            if self.active:
                return self._handle_key(event.key.keysym.sym, event.key.keysym.mod)
            return False
        return False

    def update(self, delta_time: float) -> None:
        """主循环每帧调用：驱动光标闪烁，并让 IME 候选窗口跟随光标/滚动。"""
        if self.active:
            self.cursor_timer += delta_time
            if self.cursor_timer >= self.CARET_BLINK_INTERVAL:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible
            self._update_ime_rect()

    # ---- 渲染 ----

    def set_factory(self, factory) -> None:
        """设置 TEXTURE 模式的 SpriteFactory（用于将文字 surface 转为纹理）。"""
        self._factory = factory

    def _measure_text(self, text: str) -> int:
        """用 TTF_SizeUTF8 测量文本的像素宽度。"""
        if not text:
            return 0
        font = self.font.get_ttf_font("default")
        w = ctypes.c_int(0)
        h = ctypes.c_int(0)
        sdl2.sdlttf.TTF_SizeUTF8(
            font, text.encode("utf-8"), ctypes.byref(w), ctypes.byref(h)
        )
        return w.value

    def _clamp_scroll(self, view_w: int) -> None:
        """按光标位置约束横向滚动量，保证光标完整位于可视区域内。"""
        if view_w <= 0:
            self._scroll_offset = 0
            return
        cursor_x = self._measure_text(self.text[:self.cursor_pos])
        text_end = self._measure_text(self.text) + self._measure_text(
            self.composing_text
        )
        # 滚动上界：光标右端对齐可视右缘（含光标宽度）
        max_scroll = max(0, text_end + self.CARET_WIDTH - view_w)
        # 光标可见范围：右端不越界 -> offset >= cursor_x + 光标宽 - view_w
        lo = max(0, cursor_x + self.CARET_WIDTH - view_w)
        # 左端不越界 -> offset <= cursor_x；且不滚过头 -> offset <= max_scroll
        hi = min(cursor_x, max_scroll)
        if lo > hi:  # 防御：极端窄可视区
            lo = hi = 0
        self._scroll_offset = max(lo, min(self._scroll_offset, hi))

    def _render_text_sprite(self, text: str, style: str):
        """将文本渲染为纹理精灵（surface 由 from_surface 自动释放）。"""
        surface = self.font.render_text(text, style=style)
        return self._factory.from_surface(surface, free=True)

    def _ensure_text_sprite(self):
        if self._cached_text != self.text:
            self._text_sprite = self._render_text_sprite(self.text, "default")
            self._cached_text = self.text
        return self._text_sprite

    def _ensure_composing_sprite(self):
        if self._cached_composing != self.composing_text:
            self._composing_sprite = self._render_text_sprite(
                self.composing_text, "composing"
            )
            self._cached_composing = self.composing_text
        return self._composing_sprite

    def measure(self, constraints=None):
        """首选尺寸：高度用 hint 固定（默认 40），宽度按约束。"""
        from SDLCore.ui.layout import Constraints
        if constraints is None:
            constraints = Constraints()
        w = self._hint_rect[2]
        h = self._hint_rect[3]
        if h == -1:
            h = 40
        if w == -1:
            w = constraints.max_w
        return (constraints.clamp_w(w), constraints.clamp_h(h))

    def render(self, renderer) -> None:
        if not self.visible:
            return
        x, y, w, h = self.abs_rect
        op = self._render_opacity

        # 背景 + 状态边框（先于裁剪绘制，保证完整）
        renderer.fill((x, y, w, h), apply_opacity(self.COLOR_BG, op))
        border = self.COLOR_ACTIVE if self.active else self.COLOR_NORMAL
        renderer.draw_rect((x, y, w, h), apply_opacity(border, op))

        # 可视宽度与横向滚动（文本过长时保证光标可见）
        view_w = w - 2 * self.TEXT_PADDING
        if view_w <= 0:
            return
        self._clamp_scroll(view_w)
        text_left = x + self.TEXT_PADDING - self._scroll_offset

        # 裁剪到输入框内部，超长文本不会渲染到框外
        clip = sdl2.SDL_Rect(x + 1, y + 1, w - 2, h - 2)
        set_render_clip(renderer, clip)

        # 选区高亮（半透明蓝，绘制在文本之下）
        sel = self._selection_range()
        if sel is not None:
            sel_x = self._measure_text(self.text[:sel[0]])
            sel_w = self._measure_text(self.text[:sel[1]]) - sel_x
            if sel_w > 0:
                enable_alpha_blend(renderer)
                renderer.fill(
                    (text_left + sel_x, y, sel_w, h),
                    apply_opacity(self.COLOR_SELECTION, op),
                )

        # 已上屏文本
        cursor_x = self._measure_text(self.text[:self.cursor_pos])
        if self.text:
            sprite = self._ensure_text_sprite()
            tw, th = sprite.size
            if op < 1.0:
                sdl2.SDL_SetTextureBlendMode(
                    sprite.texture, sdl2.SDL_BLENDMODE_BLEND
                )
                sdl2.SDL_SetTextureAlphaMod(
                    sprite.texture, int(255 * op)
                )
            # 注意：renderer.copy 必须显式传 dstrect，否则纹理会被拉伸到整个渲染目标
            renderer.copy(
                sprite,
                dstrect=(text_left, y + (h - th) // 2, tw, th),
            )

        # IME 组合文本（灰色半透明，绘制在光标处，透明度叠加）
        if self.composing_text:
            csprite = self._ensure_composing_sprite()
            cw, ch = csprite.size
            sdl2.SDL_SetTextureBlendMode(csprite.texture, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetTextureAlphaMod(csprite.texture, int(150 * op))
            renderer.copy(
                csprite,
                dstrect=(text_left + cursor_x, y + (h - ch) // 2, cw, ch),
            )

        # 闪烁光标（竖线）
        if self.active and self.cursor_visible:
            renderer.fill(
                (text_left + cursor_x, y + 3, self.CARET_WIDTH, h - 6),
                apply_opacity(self.COLOR_CARET, op),
            )

        # 恢复渲染裁剪
        set_render_clip(renderer, None)
