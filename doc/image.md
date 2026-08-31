# Image（图片显示控件）

**模块**：`SDLCore/ui/image.py`

## 概述

纯图片控件：显示图片纹理（PNG / SVG 等，经 `ResourceManager` 加载或直接传入纹理）。
**保持宽高比缩放并居中显示，不填充背景**——适配 logo、图标等素材。

## 构造参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `rect` | `tuple (x, y, w, h)` | 显示区域（相对父容器） |
| `path` | `str \| None` | 图片路径（经全局 `resources` 加载） |
| `texture` | `TextureSprite \| None` | 直接传入纹理（优先于 `path`） |

## 接口

- `set_texture(texture)`：运行时更换纹理。
- `texture`（属性）：当前纹理。

## 使用示例

```python
from SDLCore.ui.image import Image

img = Image((100, 100, 480, 280), path="resource/images/png/logo.png")
# 或直接传纹理
img2 = Image((100, 100, 480, 280), texture=logo_texture)
```
