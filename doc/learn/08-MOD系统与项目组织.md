# 08 MOD 系统与项目组织

目标：理解项目的 MOD 化组织方式 —— 主游戏也是 mod，第三方 mod 与之同机制。

## 1. 核心约定

```
mods/
├── base_game/       # 主游戏 mod（游戏主体，priority=0 最先加载）
│   ├── mod.json     # 元数据
│   ├── main.py      # 入口（register(api)）
│   ├── loading_scene.py / start_scene.py ...
│   └── resource/    # 素材
└── demo_mod/        # 第三方 mod（depends base_game）
```

- **主游戏逻辑也是 mod**（`base_game`），与第三方 mod 完全同机制。
- `main.py`（根）只负责：初始化 SDL2 → 加载 mods → 驱动主循环。
- **场景均写在 base_game**（游戏主体）；第三方 mod 通过 `ModAPI` 追加自己的内容。

## 2. mod.json 元数据

```json
{
  "id": "my_mod",
  "name": "我的 Mod",
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
| `entry` | 入口模块相对路径 |

## 3. 入口协议：register(api)

每个 mod 的入口约定导出 `register(api)`，由 `ModManager` 按序调用：

```python
# mods/my_mod/main.py
def register(api):
    # 1) 注册代码场景（类接收 manager 参数）
    api.register_scene("my_scene", MyScene)

    # 2) 注册配置型场景（file 相对本 mod 目录）
    api.add_scene("menu", "我的场景", "scenes/menu/scene.json",
                  bindings={"on_click": lambda: print("点击")})

    # 3) 注册自定义控件类型（供 JSON 场景按 type 使用）
    api.register_component("blink", _build_blink)

    # 4) 订阅全局事件
    api.bind_events({"mods.loaded": lambda: print("全部 mod 已加载")})
```

## 4. ModAPI 门面速查

| 方法 | 说明 |
|---|---|
| `register_scene(name, scene_cls)` | 注册代码场景类 |
| `add_scene(id, title, file, bindings)` | 注册 JSON 配置场景 |
| `register_component(type, factory)` | 注册自定义控件 |
| `bind_events(handlers)` | 订阅全局事件总线 |
| `resource_path(rel)` | mod 目录下的绝对路径 |
| `get_mod(mod_id)` | 访问其他 mod 的元数据 |

## 5. 跨 mod 资源引用

素材归 `base_game` 统一管理，其他 mod 场景用 **`@mod_id/相对路径`** 前缀引用：

```json
{
  "type": "image_button",
  "image_normal": "@base_game/resource/images/Blue/Default/button_rectangle_flat.png"
}
```

- 无前缀路径相对**当前 mod** 目录；带前缀从**指定 mod** 目录解析。

## 6. 主 mod 如何加载同目录场景模块

`mods` 目录不是 Python 包（无法相对导入），主 mod 用 `importlib` 加载场景文件：

```python
import importlib.util
import os

def _load_mod_module(api, rel):
    path = api.resource_path(rel)
    name = f"_base_game_{os.path.splitext(os.path.basename(rel))[0]}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def register(api):
    loading = _load_mod_module(api, "loading_scene.py")
    api.register_scene("loading", loading.LoadingScene)
```

## 7. 测试 mod 与双启动入口

| 入口 | 加载目录 | 用途 |
|---|---|---|
| `python main.py` | `mods/` | 正式启动（不含测试 mod） |
| `python test_main.py` | `mods/` + `test_mods/` | 开发/验证（含控件测试场景） |

`test_main.py` 通过子类化 `Game` 覆盖 `MODS_DIRS` 实现多目录加载。

下一章学习配置驱动 UI —— [第 9 章：配置驱动 UI](09-配置驱动UI.md)
