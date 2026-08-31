# Button（按钮控件）

**模块**：`SDLCore/ui/button.py`

## 概述

颜色按钮控件：三种交互状态（`ButtonState.NORMAL / HOVER / PRESSED`）对应不同背景色，
鼠标左键在按钮内按下→`PRESSED`，在按钮内释放→触发 `callback` 并恢复 `NORMAL`。
绘制为填充色矩形 + 2px 黑色边框。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `text` | `str` | | `""` | 按钮文字（当前仅存储，本阶段不渲染） |
| `callback` | `callable` | | `None` | 点击释放时调用的回调 |
| `parent` | `Widget \| None` | | `None` | 父容器 |
| `visible` / `enabled` | `bool` | | `True` | 同 `Widget` |

## 公共接口

- 继承 `Widget` 全部接口
- `set_text(text)`：更新按钮文字
- `set_callback(cb)`：设置点击回调

## 外观常量

`COLOR_NORMAL`（灰）、`COLOR_HOVER`（浅蓝）、`COLOR_PRESSED`（深蓝）、`COLOR_BORDER`（黑）、`BORDER_WIDTH`（2px）

## 使用示例

```python
from SDLCore.ui.button import Button

btn = Button((100, 100, 120, 50), text="确定", callback=lambda: print("点击"))
btn.set_callback(lambda: print("新的回调"))   # 运行时更换回调
```
