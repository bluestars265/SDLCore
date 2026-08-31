# UIBuilder（配置驱动 UI 构建器）

**模块**：`SDLCore/ui/builder.py`

## 概述

通过 JSON / dict 声明控件树，一键递归构建。**结构用配置，行为用代码**：

- 事件处理器不在 JSON 中实现，经 `bindings`（处理器名 -> 回调）由代码注入。
- 控件类型由 `ComponentRegistry` 管理，可注册自定义控件工厂扩展任意类型。
- `$ref` 复用外部组件 JSON；`override` 覆盖属性。
- 配置中的 `id` 写入控件并登记到 `builder.by_id`；`layer` 写入控件图层。
- **通用属性**：`id` / `layer` / `weight` / `opacity`（0.0~1.0）对所有类型统一生效。

## 配置格式

```json
{
  "type": "panel",
  "id": "root",
  "layer": 20,
  "rect": [100, 80, 320, 320],
  "color": [255, 255, 255, 200],
  "layout": {"type": "vbox", "spacing": 10, "padding": [10, 10, 10, 10]},
  "children": [
    {"type": "label", "id": "title", "rect": [0, 0, -1, 26], "text": "标题"},
    {"$ref": "components/ok_button.json"},
    {"$ref": "components/ok_button.json",
     "override": {"id": "cancel_btn", "text": "取消"}}
  ]
}
```

## 内置控件类型

`panel` / `button` / `image_button` / `label` / `inputbox` / `scroll_panel` / `progress_bar`
（`layout` 支持 `vbox` / `hbox` / `grid`；`w=-1` 填满可用宽度、`h=-1` 填满高度）。

## 使用

```python
from SDLCore.ui.builder import UIBuilder

builder = UIBuilder(factory=factory, resource_resolver=resolver)
root = builder.build_file("resource/scenes/demo_scene/scene.json", bindings={
    "on_ok": self._on_ok,          # 事件处理器在代码中
})
builder.by_id["ok_btn"].set_enabled(False)   # 运行时按 id 访问
```

## 自定义控件

```python
registry = ComponentRegistry()
registry.register("my_widget", lambda props, ctx: MyWidget(...))
builder = UIBuilder(factory=factory, registry=registry)
# JSON 中即可使用 {"type": "my_widget", ...}
```

## 资源路径解析

`resource_resolver(rel)` 把配置中的相对路径映射到 mod 资源目录（`ModScene` 集成时自动提供）。

## 集成

- `ModScene`（`SDLCore/scene.py`）：从 mod 场景 JSON 构建 UI + 场景切换栏。
- `ModManager`：mod 入口经 `ModAPI` 注册自定义控件到共享 `registry`，所有 mod 场景共用。
