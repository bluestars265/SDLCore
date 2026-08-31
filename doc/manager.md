# UIManager（UI 管理器）

**模块**：`SDLCore/ui/manager.py`

## 概述

UI 总控组件：
- 持有**全屏透明根面板** `root_panel`（顶层容器），通过 `resize` 随窗口尺寸实时铺满。
- 维护输入焦点 `focused_widget`（供 `InputBox` 等文本控件注册）。
- 事件分发：无坐标的 IME 文本事件（`SDL_TEXTINPUT`/`SDL_TEXTEDITING`）**直达焦点控件**；
  其余鼠标/键盘事件**逆序遍历**子控件分发，控件消费（返回 `True`）即停止。
- 递归驱动各控件的 `update` 与 `render`。

## 构造

```python
ui = UIManager()
ui.root_panel.add_child(widget)   # 挂载顶层控件
```

无需参数。

## 公共接口

| 方法 | 说明 |
|---|---|
| `resize(width, height)` | 根面板铺满全屏，递归刷新绝对坐标（**每帧调用**，支持窗口缩放） |
| `set_focus(widget)` | 注册/清空焦点控件（传 `None` 表示失焦） |
| `handle_events(events)` | 事件分发（传入 `sdl2.ext.get_events()` 的结果） |
| `update(delta_time)` | 递归调用 UI 树中各控件的 `update` |
| `render(renderer)` | 渲染整棵 UI 树 |

## 属性

| 属性 | 说明 |
|---|---|
| `root_panel` | 全屏透明 `Panel`，作为顶层容器 |
| `focused_widget` | 当前持有输入焦点的控件 |

## 使用示例

```python
from SDLCore.ui.manager import UIManager
from SDLCore.ui.button import Button

ui = UIManager()
ui.root_panel.add_child(Button((100, 100, 120, 50), text="确定"))

# 主循环中：
# ui.resize(width, height)       # 每帧，支持缩放
# ui.handle_events(events)       # 每帧，传入事件列表
# ui.update(delta_time)          # 每帧
# ui.render(renderer)            # 每帧
```
