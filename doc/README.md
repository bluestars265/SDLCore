# SDLCore UI 组件库文档

基于 **PySDL2** 的通用 GUI 控件库，位于 `SDLCore/ui/`（通用引擎层，不含任何游戏业务逻辑）。

## 安装

```bash
pip install pysdl2 pysdl2-dll        # 运行时依赖（pysdl2-dll 含 SDL_image 2.8+，支持 SVG）
pip install dist/sdlcore-0.1.0-py3-none-any.whl   # 安装引擎（构建产物见 dist/，或源码 pip install .）
```

## 文档索引

| 文档 | 组件 | 模块 | 说明 |
|---|---|---|---|
| [widget.md](widget.md) | `Widget` | `SDLCore/ui/widget.py` | 控件基类：定位/尺寸/可见性/容器/生命周期 |
| [panel.md](panel.md) | `Panel` | `SDLCore/ui/panel.py` | 容器控件：组合子控件、半透明背景 |
| [button.md](button.md) | `Button` | `SDLCore/ui/button.py` | 颜色按钮：三态 + 点击回调 |
| [imagebutton.md](imagebutton.md) | `ImageButton` | `SDLCore/ui/imagebutton.py` | 图片按钮：三态图片、资源路径 |
| [inputbox.md](inputbox.md) | `InputBox` | `SDLCore/ui/inputbox.py` | 输入框：系统 IME、光标、横向滚动 |
| [label.md](label.md) | `Label` | `SDLCore/ui/label.py` | 文字标签：任意颜色 |
| [scrollpanel.md](scrollpanel.md) | `ScrollPanel` | `SDLCore/ui/scrollpanel.py` | 滚动面板：视口裁剪 + 滚轮滚动 |
| [gridlayout.md](gridlayout.md) | `GridLayout` | `SDLCore/ui/gridlayout.py` | 网格布局容器：自动排布子控件（兼容旧类） |
| [layout.md](layout.md) | `Layout` 系列 | `SDLCore/ui/layout.py` | 布局系统：Panel 持有布局对象，支持 `-1` 自适应 |
| [progressbar.md](progressbar.md) | `ProgressBar` | `SDLCore/ui/progressbar.py` | 进度条：数值映射 + 填充/边框渲染 |
| [checkbox.md](checkbox.md) | `CheckBox` | `SDLCore/ui/checkbox.py` | 复选框：方框 + 文本 + 点击切换回调 |
| [radiogroup.md](radiogroup.md) | `RadioGroup` | `SDLCore/ui/radiogroup.py` | 单选组：圆形选项 + 互斥 + 回调 |
| [slider.md](slider.md) | `Slider` | `SDLCore/ui/slider.py` | 滑动条：点击/拖拽 + step 对齐 + 数值显示 |
| [listbox.md](listbox.md) | `ListBox` | `SDLCore/ui/listbox.py` | 列表：多选 + Ctrl/Shift + 高亮 |
| [combobox.md](combobox.md) | `ComboBox` | `SDLCore/ui/combobox.py` | 下拉选择框：浮层列表 + 头部三角 |
| [resource.md](resource.md) | `ResourceManager` | `SDLCore/resource.py` | 全局资源管理器：纹理缓存 + 异步加载 |
| [builder.md](builder.md) | `UIBuilder` | `SDLCore/ui/builder.py` | 配置驱动 UI 构建：JSON 场景 + `$ref` + bindings |
| [mod.md](mod.md) | `ModManager` | `SDLCore/modmanager.py` | MOD 系统：入口协议 + 依赖排序加载 |
| [rendering.md](rendering.md) | `BatchedRenderer` | `SDLCore/ui/batcher.py` | 渲染优化：矩形合批 + 脏标记 + 纹理缓存 |
| [manager.md](manager.md) | `UIManager` | `SDLCore/ui/manager.py` | UI 管理器：全屏根面板、焦点、事件分发 |
| [scene.md](scene.md) | `Scene` / `SceneManager` | `SDLCore/scene.py` | 场景系统：场景生命周期与管理 |
| [image.md](image.md) | `Image` | `SDLCore/ui/image.py` | 图片控件：保持宽高比居中、不填充背景 |
| [logcapture.md](logcapture.md) | `LogCapture` | `SDLCore/logcapture.py` | 命令行输出捕获：stdout 转发 + 线程安全收集 |

## 学习教程

新手从零入门 SDLCore 请阅读 **[learn/README.html](learn/README.html)**（`doc/learn/`，共 11 章，含可运行示例）。

> 本目录仅收录 **SDLCore 通用引擎层** 文档。游戏逻辑层文档
> （加载界面 / 开始界面等启动流程场景）见 `game_doc/`（游戏项目内，非本仓库发布内容）。

> 每个 `.md` 均提供同名 **HTML 版**（`*.html`，内容同步）。
> 重新生成：`python tools/md2html.py doc`（保留 `.md`，仅刷新 `.html`）。

## 通用约定

- **坐标**：`rect = (x, y, w, h)` 为**相对父容器**的坐标；`abs_rect` 为世界绝对坐标，由 `update_abs_position()` 递归计算。
- **字体资源**：文字控件默认从项目 `resource/fonts/` 目录加载字体，回退到 Windows 系统字体。
- **渲染器**：控件绘制依赖 `sdl2.ext.Renderer`（硬件加速）。文字/图片控件还需要
  `SpriteFactory(sdl2.ext.TEXTURE, renderer=...)`——可在**构造时传入 `factory` 参数**，或稍后调用 `set_factory(factory)`。
- **事件**：`handle_event(event)` 返回 `True` 表示消费该事件（停止向底层控件传递）。
- **窗口缩放**：每帧通过 `UIManager.resize(w, h)` 使根面板铺满全屏并刷新子控件绝对坐标。

## 快速开始

```python
import sdl2.ext
from SDLCore.ui.manager import UIManager
from SDLCore.ui.button import Button

# 初始化渲染器（Game 内完成）
renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_ACCELERATED)
factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)

ui = UIManager()
btn = Button((100, 100, 120, 50), text="确定", callback=lambda: print("点击"))
ui.root_panel.add_child(btn)

# 主循环中：
# ui.resize(width, height)
# ui.handle_events(events)
# ui.update(delta_time)
# ui.render(renderer)
```

## 场景系统

多界面应用建议使用 `Scene` / `SceneManager`（见 [scene.md](scene.md)）组织代码，例如本项目演示：
`main.py` → 注册 `game/scene_button.py`（按钮场景）与 `game/scene_inputbox.py`（输入框场景），
场景内通过切换按钮在两者间跳转。
