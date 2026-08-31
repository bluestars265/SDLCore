# Label（文字标签控件）

**模块**：`SDLCore/ui/label.py`

## 概述

展示不同颜色文字的标签控件：文字以 GPU 纹理渲染（TEXTURE 模式），垂直居中、左对齐；
通过 `FontTTF` 具名样式机制支持任意颜色切换。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `text` | `str` | | `""` | 显示文本 |
| `color` | `RGBA tuple` | | `(255, 255, 255, 255)` | 文字颜色 |
| `font_path` | `str` | | `None` | 字体文件路径；默认 `resource/fonts/`（回退系统字体） |
| `font_size` | `str` | | `"18px"` | 字号 |
| `parent` / `visible` / `enabled` | — | | — | 同 `Widget` |
| `factory` | `SpriteFactory` | ✅ | `None` | **TEXTURE 渲染工厂**（文字渲染必需） |

## 公共接口

- 继承 `Widget` 全部接口
- `set_text(text)`：更新显示文本
- `set_color(color)`：切换文字颜色（首次出现的颜色自动登记字体样式）
- `set_factory(factory)`：设置渲染工厂

## 使用示例

```python
from SDLCore.ui.label import Label

title = Label((20, 8, 240, 30), text="Mindustry-like TD", color=(0, 200, 200, 255), factory=factory)
hint = Label((20, 44, 240, 24), text="提示信息", color=(180, 180, 180, 255), factory=factory)
title.set_color((255, 128, 0, 255))   # 运行时改色
title.set_text("新标题")               # 运行时改文
```
