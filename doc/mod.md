# MOD 系统

**模块**：`SDLCore/modmanager.py`

## 概述

约定式 MOD 加载：每个 mod 是一个目录（含 `mod.json` 元数据 + 可选入口模块 + 场景/资源）。
**主游戏逻辑也是 mod**（`mods/base_game/`，priority=0 最先加载），与第三方 mod 同机制。

## 目录结构

```
mods/
├── base_game/                # 主游戏 mod（游戏主体，priority=0 最先加载）
│   ├── mod.json
│   ├── main.py               # 入口（register(api)，注册 loading/start 场景）
│   ├── loading_scene.py      # 开始加载界面（代码场景）
│   ├── start_scene.py        # 开始界面 / 主菜单（代码场景）
│   └── resource/…            # 素材资源（images/...，含 SVG）
└── demo_mod/                 # 演示第三方 mod（depends base_game）

test_mods/                    # 测试 mod 目录（正式启动 main.py 不加载）
└── test_game/                # 控件测试 mod（depends base_game）
```

- 正式启动：`python main.py`（仅加载 `mods/`；base_game 主 mod 优先，随后其他 mod）。
- 测试启动：`python test_main.py`（加载 `mods/` + `test_mods/`）。
- 场景（loading / start 等）均写在 base_game（游戏主体）中。

## mod.json 元数据

```json
{
  "id": "demo_mod",
  "name": "演示 Mod",
  "version": "0.1.0",
  "priority": 10,
  "depends": ["base_game"],
  "entry": "main.py"
}
```

| 字段 | 说明 |
|---|---|
| `id` | 唯一标识 |
| `priority` | 越小越先加载（`base_game` = 0） |
| `depends` | 依赖的 mod id（拓扑排序，依赖者后加载） |
| `entry` | 入口模块相对路径（如 `main.py`） |

## 入口协议

每个 mod 的入口约定导出 `register(api)`，由 `ModManager` 按序调用：

```python
# mods/demo_mod/main.py
def register(api):
    api.register_component("blink", _build_blink)        # 自定义控件
    api.add_scene("demo", "演示 Mod", "scenes/demo/scene.json",
                  bindings={"on_demo_click": lambda: print("点击")})
    api.bind_events({"event_name": handler})            # 全局事件
```

## ModAPI 门面

| 方法 | 说明 |
|---|---|
| `register_component(type_name, factory)` | 注册自定义控件类型（供 JSON 场景使用） |
| `register_scene(name, scene_cls)` | 注册代码型场景类 |
| `add_scene(scene_id, title, file, bindings)` | 注册配置型场景（file 相对 mod 目录） |
| `bind_events(handlers)` | 向全局 `EventBus` 注册处理器 |
| `resource_path(rel)` | mod 资源目录绝对路径 |
| `get_mod(mod_id)` | 访问其他 mod 元数据 |

## 加载时序

```
main.py 引擎初始化
  → ModManager.discover()（扫描 mods/，读 mod.json，priority+depends 拓扑排序）
  → ModManager.load_all()（按序调用各 mod 入口 register(api)）
  → ModManager.install_scenes()（配置场景设置切换链并注册到 SceneManager）
  → 进入首场景
```

## 配置型场景

- 场景 JSON 由 `UIBuilder` 构建（见 [builder.md](builder.md)），支持 `$ref` 组件复用、`bindings` 事件注入、`id`/`layer`。
- `ModScene`（`SDLCore/scene.py`）加载 JSON 场景并自动添加底部场景切换栏。
- 图片相对路径经 `resource_resolver` 映射到 mod 资源目录。

## 跨 mod 资源引用

素材资源归主 mod（`base_game`）统一管理，其他 mod 场景用 **`@mod_id/相对路径`** 前缀跨 mod 引用：

```json
{
  "type": "image_button",
  "image_normal": "@base_game/resource/images/Blue/Default/button_rectangle_flat.png"
}
```

- 无前缀路径相对**当前 mod** 目录解析。
- 前缀路径从**指定 mod** 目录解析（找不到该 mod 时回退相对当前 mod）。

## 边界（明确不做）

- 代码沙箱 / 隔离：约定为**可信 mod**。
- 热加载 / 运行时卸载。
- 依赖版本解析：仅 `priority + depends` 简单排序。
- mod 打包下载：文件系统即分发。
