# SDLCore

基于 **PySDL2** 的通用 GUI 引擎 + MOD 化游戏框架。

SDLCore 提供一套与具体游戏无关的可复用底层能力：GUI 控件、布局系统、场景管理、
资源管理（含 SVG）、渲染优化与 MOD 化加载机制。主游戏逻辑可作为 **MOD** 构建，
与第三方 MOD 采用完全相同的加载机制。

## ✨ 特性

- **15+ 内置控件**：`Widget` / `Panel` / `Button` / `ImageButton` / `Label` / `InputBox`
  （支持中文 IME）/ `ScrollPanel` / `CheckBox` / `RadioGroup` / `Slider` / `ListBox` /
  `ComboBox` / `ProgressBar` / `Image` / `GridLayout`
- **布局系统**：`VBox` / `HBox` / `Grid`，`-1` 自适应、`Constraints` 约束、`fit_content`
- **场景系统**：`Scene` / `SceneManager`，生命周期钩子、`shared_data` + `EventBus` 场景间通信
- **资源管理**：`ResourceManager` 纹理缓存 + 异步加载；SDL_image 2.8+ **原生支持 SVG**
- **MOD 系统**：`ModManager` / `ModAPI`，入口协议 + 依赖拓扑排序；主游戏也是 MOD
- **配置驱动 UI**：`UIBuilder` 用 JSON 声明界面、`bindings` 注入行为、`$ref` 组件复用
- **渲染优化**：`BatchedRenderer` 矩形合批（一次提交多矩形）、裁剪感知
- **硬件加速**：所有精灵基于 `SpriteFactory(TEXTURE)`（GPU 渲染）

## 📦 安装

环境要求：**Python 3.13+**、PySDL2 运行时 DLL。

```bash
# 安装运行时依赖
pip install pysdl2 pysdl2-dll

# 安装 SDLCore 引擎（本仓库构建的 wheel 或源码安装）
pip install dist/sdlcore-0.1.0-py3-none-any.whl
# 或从源码
pip install .
```

> `pysdl2-dll` 内置 SDL2 全系列 DLL（含 **SDL_image 2.8+**，支持 SVG）。无需手动设置 `PYSDL2_DLL_PATH`。

## 🚀 快速开始

```python
import sdl2
import sdl2.ext
from SDLCore.ui.manager import UIManager
from SDLCore.ui.button import Button
from SDLCore.ui.panel import Panel

def main():
    sdl2.ext.init()
    window = sdl2.ext.Window(
        "Hello SDLCore", size=(800, 600),
        flags=sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_SHOWN)
    renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_ACCELERATED)
    factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)

    ui = UIManager()
    panel = Panel((200, 150, 400, 260), color=(30, 30, 40, 230))
    panel.add_child(Button((40, 60, 180, 52), text="点击我",
                           callback=lambda: print("你好，SDLCore！")))
    ui.root_panel.add_child(panel)

    running = True
    while running:
        events = sdl2.ext.get_events()
        for e in events:
            if e.type == sdl2.SDL_QUIT:
                running = False
        w, h = window.size
        ui.resize(w, h)
        ui.handle_events(events)
        ui.update(1 / 60)
        renderer.clear((40, 44, 56))
        ui.render(renderer)
        renderer.present()
        sdl2.SDL_Delay(16)

    window.close()
    sdl2.SDL_Quit()

if __name__ == "__main__":
    main()
```

## 📚 文档

| 目录 | 内容 |
|---|---|
| [`doc/`](doc/README.md) | SDLCore 组件参考文档（控件 / 布局 / 场景 / 资源 / MOD / 渲染） |
| [`doc/learn/`](doc/learn/README.md) | **从零入门教程**（共 11 章，含可运行示例） |

## 🗂 项目结构

```
SDLCore/                 # ★ 本引擎包（仓库主体）
├── __init__.py
├── scene.py             #   场景系统（Scene / SceneManager / ModScene / EventBus）
├── resource.py          #   资源管理器（纹理缓存 + 异步加载 + SVG）
├── modmanager.py        #   MOD 系统（ModManager / ModAPI）
├── logcapture.py        #   命令行输出捕获
└── ui/                  #   控件库（widget/panel/button/...）
doc/                     # 文档（参考文档 + 从零入门教程）
```

> 本仓库仅发布 **SDLCore 引擎层**。仓库外的 `main.py` / `mods/` 是使用本引擎的
> **示例游戏项目**（塔防原型），可作为参考，但不属于引擎包。

## 🧩 依赖

| 依赖 | 说明 |
|---|---|
| `pysdl2` | Python SDL2 绑定（`sdl2` / `sdl2.ext`） |
| `pysdl2-dll` | SDL2 运行时 DLL（含 SDL_image 2.8+ → SVG 支持） |

## 📄 许可证

[Apache License 2.0](LICENSE)

---

> 构建 wheel：`python -m build --wheel`（需 `pip install build`，产物在 `dist/`）。
