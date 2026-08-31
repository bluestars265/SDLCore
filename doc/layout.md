# Layout（布局系统）

**模块**：`SDLCore/ui/layout.py`

## 概述

布局系统抽象：`Layout` 接口负责根据容器 `rect` 计算子控件的相对坐标。
**`Panel` 持有 `Layout` 实例**（组合优于继承），在 `add_child` / `remove_child` / `set_rect`
时自动调用布局排布子控件——容器与布局解耦，便于扩展新布局。

## 自适应尺寸约定

子控件 `rect` 中 `w == -1` 表示**填满父容器可用宽度**，`h == -1` 表示**填满可用高度**。
布局读子控件的原始布局意图（`_hint_rect`，构造时的 `rect`），因此即使布局后实际尺寸被覆盖，
窗口缩放触发重新布局时仍能正确自适应。

## 约束与测量（Constraints / measure）

父布局器向子控件传递 **`Constraints`**（min/max 尺寸约束），子控件通过
**`measure(constraints)`** 返回首选尺寸——Flutter/Android 风格的约束向下传递：

```python
from SDLCore.ui.layout import Constraints

c = Constraints(min_w=0, max_w=300, min_h=0, max_h=200)
c.tight(100, 50)          # 紧约束（强制尺寸）
c.loose(max_w=400)        # 松约束
c.clamp((500, 300))       # -> (300, 200)
```

| 控件 | measure 行为 |
|---|---|
| `Widget`（基类） | 按 hint 尺寸（固定 / `-1` 填满） |
| `Label` | 文字内容宽高（fit_content） |
| `Button` | `fit_content=True` 时按文字 + 内边距 |
| `ImageButton` | 图片原始尺寸 |
| `InputBox` | 固定高度（默认 40）+ 宽度按约束 |

## flex 权重（layout_weight）

`VBoxLayout` / `HBoxLayout` 支持 CSS 风格 flex 权重：子控件设置 `layout_weight`（>0），
在按内容测量后，**剩余空间按权重比例分配**：

```python
from SDLCore.ui.panel import Panel
from SDLCore.ui.layout import VBoxLayout
from SDLCore.ui.button import Button

p = Panel((0, 0, 300, 210), layout=VBoxLayout(spacing=0))
a = Button((0, 0, -1, 0)); a.layout_weight = 1   # 占 1/3（70px）
b = Button((0, 0, -1, 0)); b.layout_weight = 2   # 占 2/3（140px）
p.add_child(a); p.add_child(b)
```

> JSON 配置中可用 `"weight": 1` 声明（UIBuilder 自动写入 `layout_weight`）。

## 内置布局

| 布局 | 说明 |
|---|---|
| `GridLayout(cols, cell_width, cell_height, h_spacing, v_spacing, padding)` | 网格排列，行数自动计算；`cell_width`/`cell_height` 为 0 时均分可用尺寸 |
| `VBoxLayout(spacing, padding, align)` | 垂直堆叠；子控件 `w=-1` 填满宽度；`align` 取 `stretch/left/center/right` |
| `HBoxLayout(spacing, padding, align)` | 水平排列；子控件 `h=-1` 填满高度；`align` 取 `stretch/top/center/bottom` |

## Panel 集成接口

| 成员 | 说明 |
|---|---|
| `Panel(rect, layout=...)` | 构造时传入布局对象 |
| `set_layout(layout)` | 运行时设置/更换布局并立即排布 |
| `layout`（属性） | 当前布局对象（`None` 表示自由定位） |

## 使用示例

```python
from SDLCore.ui.panel import Panel
from SDLCore.ui.layout import VBoxLayout, HBoxLayout, GridLayout
from SDLCore.ui.button import Button
from SDLCore.ui.label import Label

# 垂直布局：子控件 w=-1 自动填满宽度
panel = Panel((100, 100, 300, 260), color=(255, 255, 255, 200),
              layout=VBoxLayout(spacing=10, padding=(10, 10, 10, 10)))
panel.add_child(Label((0, 0, -1, 26), text="标题", factory=factory))
panel.add_child(Button((0, 0, -1, 44), text="按钮"))

# 水平布局：子控件 h=-1 自动填满高度
bar = Panel((100, 380, 300, 60), layout=HBoxLayout(spacing=8, padding=(6, 6, 6, 6)))
bar.add_child(Button((0, 0, 90, -1), text="确定"))
bar.add_child(Button((0, 0, 90, -1), text="取消"))

# 网格布局（新用法）
grid = Panel((0, 0, 300, 200), layout=GridLayout(cols=3, h_spacing=8, v_spacing=8))
grid.add_child(Button((0, 0, 0, 0)))  # 尺寸由网格自动分配
```

> 旧容器类 `GridLayout(Panel)`（`SDLCore/ui/gridlayout.py`）仍可用作向后兼容，
> 内部已改用新布局对象驱动；推荐新代码使用 `Panel(rect, layout=...)` 组合方式。
