# ImageButton（图片按钮控件）

**模块**：`SDLCore/ui/imagebutton.py`

## 概述

继承 `Button`。三种状态（常态/悬停/按下）各分配一张图片，图片被**缩放（拉伸）到按钮矩形大小**；
某状态未配置图片时，该状态自动回退为 `Button` 的颜色渲染。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `image_normal` | `str`（图片路径） | ✅ | `None` | **常态图片**（推荐必须） |
| `image_hover` | `str`（图片路径） | | `None` | 悬停图片 |
| `image_pressed` | `str`（图片路径） | | `None` | 按下图片 |
| `text` | `str` | | `""` | **可选文字**（非空且 `factory` 可用时居中显示） |
| `text_color` | `RGBA` | | `(255,255,255,255)` | 文字颜色 |
| `callback` | `callable` | | `None` | 点击回调 |
| `parent` / `visible` / `enabled` | — | | — | 同 `Widget` |
| `factory` | `SpriteFactory` | ✅ | `None` | **TEXTURE 渲染工厂**；传入则立即加载三态图片（文字渲染也依赖） |

## 公共接口

- 继承 `Button`（`set_text` / `set_callback` / `set_position` 等）
- `set_factory(factory)`：设置工厂并加载三态图片纹理

## 使用示例

```python
from SDLCore.ui.imagebutton import ImageButton

btn = ImageButton(
    (100, 100, 160, 50),
    text="开始游戏",                    # 可选文字（居中）
    text_color=(255, 255, 255, 255),
    image_normal="resource/images/Blue/Default/button_rectangle_flat.png",
    image_hover="resource/images/Blue/Default/button_rectangle_gradient.png",
    image_pressed="resource/images/Blue/Default/button_rectangle_depth_flat.png",
    callback=lambda: print("点击"),
    factory=factory,          # SpriteFactory(TEXTURE)
)

# text 为空则不渲染文字，仅显示图片
btn2 = ImageButton((100, 180, 160, 50),
                   image_normal="resource/images/Blue/Default/button_rectangle_flat.png",
                   factory=factory)

# SVG 矢量素材（SDL_image 2.8+ 支持 .svg，渲染时拉伸到按钮大小）
btn3 = ImageButton((100, 260, 180, 56),
                   text="SVG 按钮",
                   image_normal="resource/images/svg/按钮框.svg",
                   image_hover="resource/images/svg/按钮框_悬停.svg",
                   factory=factory)
```

> 提示：三态图片路径应指向项目 `resource/images/` 下的素材，支持 PNG / SVG 等格式。
> JSON 配置可用 `"text"` / `"text_color"` 声明文字；mod 场景中跨 mod 引用素材用
> `"@base_game/resource/images/..."` 前缀。
