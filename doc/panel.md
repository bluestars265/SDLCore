# Panel（容器控件）

**模块**：`SDLCore/ui/panel.py`

## 概述

纯粹的容器控件：绘制半透明背景后，依次渲染所有可见子控件；事件逆序分发给子控件（消费即停止）。
子控件的 `rect` 为**相对 Panel** 的坐标，渲染时自动转换为世界绝对坐标。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `color` | `RGBA tuple` | | `(30, 30, 30, 200)` | 背景色（半透明效果） |
| `layout` | `Layout \| None` | | `None` | 布局对象（Grid/VBox/HBox，见 [layout.md](layout.md)） |
| `parent` | `Widget \| None` | | `None` | 父容器 |
| `visible` / `enabled` | `bool` | | `True` | 同 `Widget` |

## 布局支持

- `Panel(rect, layout=GridLayout(...))`：`add_child` / `remove_child` / `set_rect` 自动排布子控件。
- 子控件 `rect` 中 `w=-1` 填满可用宽度（VBox）、`h=-1` 填满可用高度（HBox）。
- `set_layout(layout)` 运行时更换布局；`layout` 属性访问当前布局对象。

## 公共接口

继承 `Widget` 全部接口，`add_child(widget)` 由基类提供。

## 使用示例

```python
from SDLCore.ui.panel import Panel
from SDLCore.ui.button import Button
from SDLCore.ui.inputbox import InputBox

panel = Panel((100, 100, 240, 160), color=(255, 255, 255, 200))  # 半透明白色
box = InputBox((20, 20, 200, 40), on_submit=lambda t: print(t), factory=factory)
btn = Button((70, 80, 100, 50), text="确定")
panel.add_child(box)   # box 绝对坐标 = (120, 120)
panel.add_child(btn)
```
