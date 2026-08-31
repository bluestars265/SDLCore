# -*- coding: utf-8 -*-
"""Layout：布局系统抽象（通用引擎层，与具体游戏无关）。

设计要点：
- ``Layout`` 为抽象接口：根据容器的 ``rect`` 与子控件，为每个子控件计算相对坐标。
- ``Panel`` 持有 ``Layout`` 实例（组合优于继承），在 add_child / remove_child / set_rect
  时自动调用布局排布子控件。
- 自适应尺寸约定：子控件 ``rect`` 中 ``w == -1`` 表示**填满可用宽度**（由 VBox 等解析），
  ``h == -1`` 表示**填满可用高度**（由 HBox 等解析）。

内置布局：
- ``GridLayout``：网格排列（行数自动计算，单元格可均分或固定尺寸）。
- ``VBoxLayout``：垂直堆叠，子控件默认填满宽度（``w == -1``）。
- ``HBoxLayout``：水平排列，子控件默认填满高度（``h == -1``）。
"""


_INF = 1 << 30


class Constraints:
    """尺寸约束：由父容器传递给子控件的测量约束（Flutter/Android 风格）。

    子控件在 ``measure(constraints)`` 中根据约束与自身内容决定首选尺寸。
    """

    __slots__ = ("min_w", "max_w", "min_h", "max_h")

    def __init__(self, min_w=0, max_w=_INF, min_h=0, max_h=_INF):
        self.min_w = max(0, int(min_w))
        self.max_w = max(self.min_w, int(max_w))
        self.min_h = max(0, int(min_h))
        self.max_h = max(self.min_h, int(max_h))

    @staticmethod
    def tight(w, h):
        """紧约束：min == max（强制尺寸）。"""
        return Constraints(w, w, h, h)

    @staticmethod
    def loose(max_w=_INF, max_h=_INF):
        """松约束：0 ~ max。"""
        return Constraints(0, max_w, 0, max_h)

    def clamp_w(self, w: int) -> int:
        return max(self.min_w, min(int(w), self.max_w))

    def clamp_h(self, h: int) -> int:
        return max(self.min_h, min(int(h), self.max_h))

    def clamp(self, size):
        return (self.clamp_w(size[0]), self.clamp_h(size[1]))

    def deflate(self, left, top, right, bottom):
        """内缩约束（用于 padding）。"""
        return Constraints(
            max(0, self.min_w - left - right),
            max(0, self.max_w - left - right),
            max(0, self.min_h - top - bottom),
            max(0, self.max_h - top - bottom),
        )

    def __repr__(self):
        return (f"Constraints(min_w={self.min_w}, max_w={self.max_w}, "
                f"min_h={self.min_h}, max_h={self.max_h})")


class Layout:
    """布局接口。"""

    def layout(self, container) -> None:
        """计算并设置 container 各子控件的相对坐标。"""
        raise NotImplementedError


class GridLayout(Layout):
    """网格布局：按指定列数排布，行数 = ceil(子控件数 / 列数)。"""

    def __init__(
        self,
        cols: int = 1,
        cell_width: int = 0,
        cell_height: int = 0,
        h_spacing: int = 5,
        v_spacing: int = 5,
        padding=(5, 5, 5, 5),
    ) -> None:
        self.cols = max(1, int(cols))
        self.cell_width = int(cell_width)    # 0 表示自动均分宽度
        self.cell_height = int(cell_height)  # 0 表示自动均分高度
        self.h_spacing = int(h_spacing)
        self.v_spacing = int(v_spacing)
        self.padding = tuple(padding)        # (left, top, right, bottom)

    def layout(self, container) -> None:
        children = [c for c in container.children if c.visible]
        n = len(children)
        if n == 0:
            return
        rows = (n + self.cols - 1) // self.cols
        avail_w = max(0, container.rect[2] - self.padding[0] - self.padding[2])
        avail_h = max(0, container.rect[3] - self.padding[1] - self.padding[3])
        cell_w = (
            self.cell_width if self.cell_width > 0
            else max(0, (avail_w - self.h_spacing * (self.cols - 1)) // self.cols)
        )
        cell_h = (
            self.cell_height if self.cell_height > 0
            else max(0, (avail_h - self.v_spacing * (rows - 1)) // rows)
        )
        for i, child in enumerate(children):
            col, row = i % self.cols, i // self.cols
            child.set_rect((
                self.padding[0] + col * (cell_w + self.h_spacing),
                self.padding[1] + row * (cell_h + self.v_spacing),
                cell_w,
                cell_h,
            ))


class VBoxLayout(Layout):
    """垂直堆叠布局：子控件自上而下排列，``w == -1`` 时填满可用宽度。"""

    def __init__(
        self,
        spacing: int = 5,
        padding=(0, 0, 0, 0),
        align: str = "stretch",
    ) -> None:
        self.spacing = int(spacing)
        self.padding = tuple(padding)
        self.align = align  # stretch / left / center / right

    def layout(self, container) -> None:
        children = [c for c in container.children if c.visible]
        if not children:
            return
        avail_w = max(0, container.rect[2] - self.padding[0] - self.padding[2])
        avail_h = max(0, container.rect[3] - self.padding[1] - self.padding[3])
        # 子控件测量约束：宽度上限为可用宽，高度宽松（由内容/权重决定）
        measure_c = Constraints(0, avail_w, 0, _INF)
        infos = []
        total_fixed_h = 0
        total_weight = 0
        for child in children:
            pw, ph = child.measure(measure_c)
            weight = max(0, getattr(child, "layout_weight", 0) or 0)
            infos.append((child, pw, ph, weight))
            total_weight += weight
            if weight <= 0:
                total_fixed_h += ph
        remaining = (
            avail_h - total_fixed_h - self.spacing * max(0, len(children) - 1)
        )
        y = self.padding[1]
        for child, pw, ph, weight in infos:
            # 宽度：stretch 填满；否则按内容宽 + 对齐
            if self.align == "stretch":
                cw = avail_w
                x = self.padding[0]
            else:
                cw = min(pw, avail_w)
                if self.align == "center":
                    x = self.padding[0] + (avail_w - cw) // 2
                elif self.align == "right":
                    x = container.rect[2] - self.padding[2] - cw
                else:  # left
                    x = self.padding[0]
            # 高度：flex 权重分配剩余空间；否则用内容首选高度
            if weight > 0 and total_weight > 0 and remaining > 0:
                ch = int(remaining * weight / total_weight)
            else:
                ch = ph
            child.set_rect((x, y, cw, ch))
            y += ch + self.spacing


class HBoxLayout(Layout):
    """水平排列布局：子控件从左到右排列，``h == -1`` 时填满可用高度。"""

    def __init__(
        self,
        spacing: int = 5,
        padding=(0, 0, 0, 0),
        align: str = "stretch",
    ) -> None:
        self.spacing = int(spacing)
        self.padding = tuple(padding)
        self.align = align  # stretch / top / center / bottom

    def layout(self, container) -> None:
        children = [c for c in container.children if c.visible]
        if not children:
            return
        avail_w = max(0, container.rect[2] - self.padding[0] - self.padding[2])
        avail_h = max(0, container.rect[3] - self.padding[1] - self.padding[3])
        # 子控件测量约束：高度上限为可用高，宽度宽松（由内容/权重决定）
        measure_c = Constraints(0, _INF, 0, avail_h)
        infos = []
        total_fixed_w = 0
        total_weight = 0
        for child in children:
            pw, ph = child.measure(measure_c)
            weight = max(0, getattr(child, "layout_weight", 0) or 0)
            infos.append((child, pw, ph, weight))
            total_weight += weight
            if weight <= 0:
                total_fixed_w += pw
        remaining = (
            avail_w - total_fixed_w - self.spacing * max(0, len(children) - 1)
        )
        x = self.padding[0]
        for child, pw, ph, weight in infos:
            # 高度：stretch 填满；否则按内容高 + 对齐
            if self.align == "stretch":
                ch = avail_h
                y = self.padding[1]
            else:
                ch = min(ph, avail_h)
                if self.align == "center":
                    y = self.padding[1] + (avail_h - ch) // 2
                elif self.align == "bottom":
                    y = container.rect[3] - self.padding[3] - ch
                else:  # top
                    y = self.padding[1]
            # 宽度：flex 权重分配剩余空间；否则用内容首选宽度
            if weight > 0 and total_weight > 0 and remaining > 0:
                cw = int(remaining * weight / total_weight)
            else:
                cw = pw
            child.set_rect((x, y, cw, ch))
            x += cw + self.spacing
