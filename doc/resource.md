# ResourceManager（资源管理器）

**模块**：`SDLCore/resource.py`

## 概述

全局纹理资源管理器：统一缓存外部图片纹理（`TextureSprite`），避免重复加载。
`ImageButton` / `ProgressBar` 等使用外部图片的控件默认经其读取资源。

## 格式支持（含 SVG）

经 SDL_image（`IMG_Load`）解码，支持 **PNG / JPG / BMP / GIF / TGA / SVG** 等格式：

- **SVG**：SDL_image 2.8+ 内置矢量光栅化（pysdl2-dll 2.32.10 实测可用）。
  组件传入 `.svg` 路径即可加载；SVG 按原始尺寸光栅化，渲染时由组件拉伸到目标矩形。
- 同步与异步加载对 SVG 同样适用。

## 设计要点

- **同步加载**：`get(path)` 缓存命中直接返回，否则立即加载并缓存。
- **异步加载**：`load_async(path)` 在**后台线程**用 `IMG_Load` 解码为 `SDL_Surface`；
  主线程每帧调用 `process_pending()` 将就绪的 surface 转为纹理并缓存。
- **线程约束**：SDL 纹理必须在主线程（渲染线程）创建，因此异步仅负责后台解码，
  纹理创建统一由主线程 `process_pending()` 完成（线程安全，内部使用锁保护）。

## 公共接口

| 方法 | 说明 |
|---|---|
| `set_factory(factory)` | 设置 TEXTURE 渲染工厂 |
| `factory`（属性） | 当前渲染工厂 |
| `get(path)` | 同步获取纹理（缓存命中复用） |
| `has(path)` | 是否已缓存 |
| `load_async(path)` | 后台线程异步解码图片 |
| `process_pending()` | 主线程调用：将后台完成解码的图片转为纹理并缓存 |

## 全局实例

```python
from SDLCore.resource import resources   # 全局默认实例
resources.set_factory(factory)            # 应用启动时注册渲染工厂
```

> 全局实例面向单渲染器应用；多渲染器场景可各自创建 `ResourceManager(factory=...)`。

## 与控件集成

- `ImageButton`、`ProgressBar` 构造时若传 `factory`，会自动将其注册到全局资源管理器并加载图片。
- 也可显式传入 `resources=自定义实例` 覆盖默认。

## 使用示例

```python
from SDLCore.resource import resources

# 同步（缓存）
tex = resources.get("resource/images/foo.png")

# 异步（后台解码，主循环每帧 process_pending 后可用）
resources.load_async("resource/images/bar.png")
# ... 主循环中： resources.process_pending()
if resources.has("resource/images/bar.png"):
    tex = resources.get("resource/images/bar.png")
```
