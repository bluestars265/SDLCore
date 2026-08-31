# Slider（滑动条控件）

**模块**：`SDLCore/ui/slider.py`

## 概述

继承 `Widget` 的水平滑动条：灰色轨道贯穿控件宽度，滑块垂直居中（内部维护 `_thumb_rect`）。
支持**点击轨道跳转**与**拖拽滑块**；数值按 `step` 步长四舍五入对齐并钳制在 `[min_val, max_val]`。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `min_val` | `float` | | `0.0` | 最小值 |
| `max_val` | `float` | | `100.0` | 最大值（`<= min` 时自动 `min+1`） |
| `value` | `float` | | `0.0` | 当前值（自动按 step 对齐） |
| `step` | `float` | | `1.0` | 步长（四舍五入对齐） |
| `on_value_changed` | `callable` | | `None` | 交互后回调 `on_value_changed(value)` |
| `factory` | `SpriteFactory` | | `None` | TEXTURE 渲染工厂（数值文本可选） |
| `id` / `layer` / `layout_weight` | — | | — | 同 `Widget` |

## 交互

- **点击轨道**：按点击 X 对应比例设置 `value` 并回调。
- **拖拽滑块**：`MOUSEBUTTONDOWN`（滑块上）设 `_dragging=True` → `MOUSEMOTION` 更新 → `MOUSEBUTTONUP` 结束。
- `set_value(value)`：外部设置（**不触发回调**，按 step 对齐）。

## 渲染

灰色轨道（左缘到右缘）→ 起点到滑块中心的主题色填充条 → 滑块（含描边）→
滑块正上方当前数值文本（`Label`，需 `factory`）。

## 使用示例

```python
from SDLCore.ui.slider import Slider

sl = Slider((100, 100, 240, 26), min_val=0, max_val=100, value=50,
            step=5, on_value_changed=lambda v: print(f"数值: {v}"),
            factory=factory)
sl.set_value(42)   # 外部设置（不回调）
```

> JSON 配置（UIBuilder）：`{"type": "slider", "id": "sl1", "rect": [0,0,0,30],
> "min": 0, "max": 10, "value": 3, "step": 1, "on_value_changed": "on_change"}`。
