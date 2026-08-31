# -*- coding: utf-8 -*-
"""GridLayout：网格布局容器（继承 Panel，向后兼容旧接口）。

- 内部使用 ``SDLCore.ui.layout.GridLayout`` 布局对象驱动排布。
- 子控件按指定列数网格排列，行数自动计算；
  添加 / 移除子控件、或自身尺寸变化时自动重新布局。
- 推荐新代码直接使用 ``Panel(rect, layout=GridLayout(...))``。
"""

from SDLCore.ui.panel import Panel
from SDLCore.ui.layout import GridLayout as GridLayoutLayout


class GridLayout(Panel):
    """按网格自动排列子控件的面板（兼容旧用法）。"""

    def __init__(
        self,
        rect,
        cols: int = 1,
        cell_width: int = 0,
        cell_height: int = 0,
        h_spacing: int = 5,
        v_spacing: int = 5,
        padding=(5, 5, 5, 5),
        parent=None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        layout = GridLayoutLayout(
            cols=cols,
            cell_width=cell_width,
            cell_height=cell_height,
            h_spacing=h_spacing,
            v_spacing=v_spacing,
            padding=padding,
        )
        super().__init__(
            rect,
            parent=parent,
            visible=visible,
            enabled=enabled,
            layout=layout,
        )

    def relayout(self) -> None:
        """手动触发重新布局（等价旧接口 layout()）。"""
        if self._layout is not None:
            self._layout.layout(self)

