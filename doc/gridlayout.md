# GridLayout（网格布局容器）

**模块**：`SDLCore/ui/gridlayout.py`

## 概述

继承 `Panel` 的网格布局容器：子控件按指定列数自动网格排列，行数由子控件数量自动计算
（`rows = ceil(子控件数 / cols)`）。添加 / 移除子控件、或自身尺寸变化时自动重新布局。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `cols` | `int` | | `1` | 列数（行数自动计算） |
| `cell_width` | `int` | | `0` | 固定单元格宽度；`0` 表示自动均分父容器宽度 |
| `cell_height` | `int` | | `0` | 固定单元格高度；`0` 表示自动均分父容器高度 |
| `h_spacing` | `int` | | `5` | 水平间距（px） |
| `v_spacing` | `int` | | `5` | 垂直间距（px） |
| `padding` | `tuple (left, top, right, bottom)` | | `(5, 5, 5, 5)` | 内边距 |
| `parent` / `visible` / `enabled` | — | — | — | 同 `Widget` |

## 尺寸计算规则

- 可用宽度 = `容器宽 - padding.left - padding.right`
- 可用高度 = `容器高 - padding.top - padding.bottom`
- `cell_width == 0`：`(可用宽度 - h_spacing × (cols - 1)) // cols`
- `cell_height == 0`：`(可用高度 - v_spacing × (rows - 1)) // rows`
- 第 `i` 个控件：`row = i // cols`，`col = i % cols`
  - `x = padding.left + col × (cell_width + h_spacing)`
  - `y = padding.top + row × (cell_height + v_spacing)`

## 公共接口

- 继承 `Panel` / `Widget` 全部接口
- `relayout()`：手动触发重新布局（添加/移除/尺寸变化时自动调用）

## 使用示例

```python
from SDLCore.ui.gridlayout import GridLayout
from SDLCore.ui.button import Button

grid = GridLayout((50, 50, 300, 200), cols=2, h_spacing=10, v_spacing=10)
for i in range(6):
    grid.add_child(Button((0, 0, 0, 0), text=f"按钮{i}"))   # 位置/大小由布局自动分配

grid.relayout()   # 需要时可手动重排
```
