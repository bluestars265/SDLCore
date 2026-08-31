# ScrollPanel（滚动面板）

**模块**：`SDLCore/ui/scrollpanel.py`

## 概述

继承 `Panel` 的滚动容器：内部维护一个 `content` 子面板，所有 `add_child` 的控件挂载到 `content`；
渲染时裁剪到视口（超出部分不可见）。支持**垂直与水平滚动**：滚轮（`wheel.y` 垂直、`wheel.x` 水平）
或**拖拽滚动条滑块**（鼠标按下滑块拖动）。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **可视区域（视口）的位置与大小** |
| `content_size` | `tuple (w, h) \| None` | | `None` | 内容区域大小；`None` 时按子控件尺寸自动计算 |
| `scroll_speed` | `float` | | `30.0` | 滚轮滚动速度（像素/刻度） |
| `show_v_scrollbar` | `bool` | | `True` | 显示垂直滚动条 |
| `show_h_scrollbar` | `bool` | | `True` | 显示水平滚动条 |
| `scrollbar_width` | `int` | | `8` | 滚动条宽度（px） |
| `track_color` | `RGBA` | | `(80,80,80,120)` | 轨道颜色（半透明） |
| `thumb_color` | `RGBA` | | `(160,160,160,220)` | 滑块颜色（纯色模式） |
| `thumb_image` | `str \| None` | | `None` | 垂直滑块图片路径（未传则纯色） |
| `thumb_image_h` | `str \| None` | | `None` | 水平滑块图片路径（未传则共用 `thumb_image` 或纯色） |
| `factory` | `SpriteFactory \| None` | | `None` | TEXTURE 渲染工厂（使用图片滑块时传入） |
| `parent` / `visible` / `enabled` | — | | — | 同 `Widget` |

## 公共接口

- 继承 `Panel` / `Widget` 全部接口
- `add_child(widget)` / `remove_child(widget)`：挂载到内部 `content`（重定向）
- `get_content()`：返回内部 `content` 面板引用
- `scroll_to(x, y)`：滚动到指定偏移（自动钳制到 `[0, content - viewport]`）

## 属性

`scroll_x` / `scroll_y`（浮动偏移，初始 0）、`content`（内部内容面板）、
`content_size`、`scroll_speed`、`show_v_scrollbar` / `show_h_scrollbar`、`thumb_image` / `thumb_image_h`

## 使用示例

```python
from SDLCore.ui.scrollpanel import ScrollPanel
from SDLCore.ui.button import Button

# 纯色滑块（默认）
sp = ScrollPanel((50, 50, 200, 300), content_size=None)
for i in range(20):
    sp.add_child(Button((10, i * 60, 180, 50), text=f"第 {i} 项"))

# 图片滑块（垂直 + 水平共用一张图）
sp2 = ScrollPanel((50, 380, 200, 120), content_size=(400, 800),
                  thumb_image="mods/base_game/resource/images/Blue/Default/button_rectangle_flat.png",
                  factory=factory)

# 交互：滚轮滚动，或鼠标拖拽滚动条滑块
```

