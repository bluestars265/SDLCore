# Widget（控件基类）

**模块**：`SDLCore/ui/widget.py`

## 概述

所有 GUI 控件的抽象基类，定义通用接口：坐标定位、可见性/可用性、容器管理、生命周期钩子。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **相对父容器的位置与大小** |
| `parent` | `Widget \| None` | | `None` | 父容器 |
| `visible` | `bool` | | `True` | 是否可见（影响渲染与事件） |
| `enabled` | `bool` | | `True` | 是否可用（禁用后不接收事件） |

## 属性

`rect`（相对坐标）、`abs_rect`（绝对坐标）、`parent`、`children`、`visible`、`enabled`

## 公共接口

| 方法 | 说明 |
|---|---|
| `update_abs_position(px, py)` | 递归刷新本控件及所有子控件的绝对坐标 |
| `set_rect(rect)` | 设置相对矩形，并刷新绝对坐标（含子控件） |
| `set_position(x, y)` | 仅改变位置（宽高不变） |
| `set_size(w, h)` | 仅改变宽高（位置不变） |
| `set_visible(visible)` | 切换可见性 |
| `set_enabled(enabled)` | 切换可用性 |
| `set_opacity(opacity)` | 设置透明度（0.0 全透明 ~ 1.0 不透明） |
| `add_child(widget)` | 挂载子控件，立即刷新其绝对坐标 |
| `remove_child(widget)` | 移除子控件并解除父子关系 |
| `handle_event(event) -> bool` | 事件处理，返回 `True` 表示消费；内置 `MOUSEMOTION` 悬停跟踪 |
| `update(delta_time)` | 每帧更新（子类可重写） |
| `render(renderer)` | 绘制（由子类实现） |

## 悬停钩子

基类通过 `_update_hover(px, py)` 维护 `_hovered` 状态（利用 `_contains` 判定），
鼠标**进入/离开**控件时各调用一次对应钩子，便于实现提示框等悬停交互：

| 钩子 | 说明 |
|---|---|
| `on_mouse_enter()` | 鼠标进入控件时调用（子类可重写） |
| `on_mouse_leave()` | 鼠标离开控件时调用（子类可重写） |

> 说明：未重写 `handle_event` 的控件自动获得悬停跟踪；重写了 `handle_event`
> 的控件（如 `Button`、`InputBox`）需在自身 `MOUSEMOTION` 分支调用
> `self._update_hover(x, y)` 以启用钩子（这些内置控件已默认接入）。

## 透明度支持

所有控件（`Panel` / `Button` / `ImageButton` / `Label` / `InputBox` / `CheckBox` /
`RadioGroup` / `Slider` / `ListBox` / `ComboBox` / `ScrollPanel` / `ProgressBar` / `GridLayout`）
均支持**整体透明度**：

- 调用 `widget.set_opacity(0.0~1.0)` 或直接设 `widget.opacity`。
- 影响该控件**直接绘制的全部元素**：纯色填充 / 边框 / 对勾 / 三角 / 文字 / 图片纹理。
- **透明度沿容器子树传播**：父容器 `opacity × 子控件 opacity` 为子控件的有效渲染透明度
  （如 `Panel` 半透明时，其内所有子控件同时变半透明）。

```python
panel = Panel((0, 0, 300, 200))
panel.set_opacity(0.6)                     # 面板整体半透明（背景 + 子控件）

btn = Button((10, 10, 100, 40), text="确定")
btn.set_opacity(0.5)                       # 按钮自身半透明

# 组合：按钮最终有效透明度 = 0.6 × 0.5 = 0.3
panel.add_child(btn)
```

> 实现：颜色 alpha 经 `apply_opacity(color, opacity)` 调制；纹理经
> `SDL_SetTextureAlphaMod` + `SDL_BLENDMODE_BLEND` 调制。半透明颜色会被
> `BatchedRenderer` 自动移出合批单独绘制，保证混合正确。


## 使用示例



```python
from SDLCore.ui.button import Button

btn = Button((10, 20, 100, 40), text="确定")   # 必要参数：位置 + 大小
btn.set_position(50, 60)                        # 移动
btn.set_size(120, 48)                           # 缩放
btn.set_visible(True)                           # 显隐
btn.set_enabled(False)                          # 禁用
```
