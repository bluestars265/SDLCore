# ProgressBar（进度条控件）

**模块**：`SDLCore/ui/progressbar.py`

## 概述

继承 `Widget` 的横向进度条：数值映射（`min`~`max`）、背景 + 进度填充 + 边框渲染。
填充宽度 = `进度比 × 控件宽度`，从左侧开始。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `min` | `float` | | `0.0` | 最小值 |
| `max` | `float` | | `100.0` | 最大值（`max <= min` 时自动设为 `min + 1`） |
| `value` | `float` | | `0.0` | 当前值（自动钳制在 `[min, max]`） |
| `bg_color` | `RGBA tuple` | | `(40, 40, 40, 255)` | 背景色 |
| `fill_color` | `RGBA tuple` | | `(0, 200, 80, 255)` | 填充色 |
| `border_color` | `RGBA tuple` | | `(80, 80, 80, 255)` | 边框色 |
| `border_width` | `int` | | `1` | 边框宽度（px） |
| `show_text` | `bool` | | `False` | 是否显示百分比文字（本阶段预留，`text_sprite` 供后续集成） |
| `fill_image` | `str \| None` | | `None` | 填充纹理图片路径；非空时替代 `fill_color` |
| `indicator_image` | `str \| None` | | `None` | 前端标记图片路径（如箭头），绘制在进度末端随进度移动 |
| `factory` | `SpriteFactory \| None` | | `None` | TEXTURE 渲染工厂（使用图片时必需传入） |
| `parent` / `visible` / `enabled` | — | — | — | 同 `Widget` |

> 说明：`fill_image` 会拉伸适配填充矩形，无需关心原始尺寸；`indicator_image` 保持图片原始宽高比，
> 中心对齐到填充末端、垂直居中。图片加载失败或未传 `factory` 时打印警告并回退为纯色模式。

## 公共接口

| 方法 | 说明 |
|---|---|
| `set_value(val)` | 更新当前值（自动钳制） |
| `set_range(min_val, max_val)` | 更新范围，并调整当前值适应新范围 |
| `get_progress()` | 返回 `0.0 ~ 1.0` 的进度比 `(value - min) / (max - min)` |
| `set_bg_color(color)` / `set_fill_color(color)` / `set_border_color(color)` | 运行时修改样式（渲染自动生效） |
| `set_factory(factory)` | 运行时设置渲染工厂并重新加载图片 |

## 属性

`min`、`max`、`value`（可直接读写）、`text_sprite`（预留）

## 使用示例

```python
from SDLCore.ui.progressbar import ProgressBar

pb = ProgressBar((50, 50, 300, 30), value=0, min=0, max=100)
pb.set_value(65)                 # 进度 65%
pb.set_range(0, 200)             # 调整范围
pb.set_fill_color((0, 150, 255, 255))  # 改填充色

# 每帧渲染：pb.render(renderer)
```
