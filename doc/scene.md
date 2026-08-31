# Scene / SceneManager（场景系统）

**模块**：`SDLCore/scene.py`

## 概述

场景化管理框架：
- **`Scene`**：一个独立界面。每个场景拥有自己的 `UIManager`（UI 树），并通过
  `on_enter` / `on_exit` / `on_resize` 管理生命周期。**Scene 仅提供生命周期管理，
  不内置任何具体 UI 辅助方法——UI 树完全由子类在 `on_enter`（或构造时）自行构建。**
- **`SceneManager`**：按名称注册/切换场景，并把 `resize` / `handle_events` / `update` / `render`
  转发给当前场景。

> 项目演示场景的标题/说明/切换按钮等辅助能力位于游戏层 `game/scene_common.py`
> （`DemoScene` 基类），不属于通用引擎层。

## Scene

### 构造参数

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `manager` | `SceneManager` | ✅ | 所属场景管理器；`self.game` 可访问宿主（window / factory 等） |

### 生命周期钩子

| 钩子 | 说明 |
|---|---|
| `on_enter()` | 进入场景时调用（可在此构建 UI 树） |
| `on_exit()` | 离开场景时调用（默认关闭系统输入法并清空输入焦点） |
| `on_resize(w, h)` | 窗口尺寸变化时由 `resize` 自动调用（空实现，子类可按需重写，例如重新计算布局） |

### 转发方法

`resize(w, h)` / `handle_events(events)` / `update(delta_time)` / `render(renderer)`
→ 全部转发给场景自身的 `self.ui`；其中 `resize` 还会调用 `on_resize(w, h)` 钩子。

## 场景间通信

`SceneManager` 提供两种跨场景通信机制（各场景可通过 `self.manager.shared_data` / `self.manager.events`
或便捷属性 `self.shared_data` / `self.events` 访问）：

### 共享数据模型（`shared_data`）

普通 `dict`，所有场景共享同一对象，跨场景读写：

```python
self.shared_data["score"] = 100          # 本场景写入
other = self.manager.shared_data["score"]  # 其他场景读取
```

### 事件总线（`events`，`EventBus`）

发布 / 订阅机制（`on` / `off` / `emit` / `clear` / `has_listeners`）：

```python
def on_player_died(self, name):
    ...

self.events.on("player_died", self.on_player_died)   # 订阅
self.events.emit("player_died", "boss")               # 发布
self.events.off("player_died", self.on_player_died)   # 取消（建议在 on_exit 中清理）
```

> 事件处理器需要自行管理生命周期：建议在 `on_enter` 订阅、`on_exit` 取消，
> 避免切换场景后残留订阅。

## SceneManager

### 构造参数

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `game` | `object \| None` | | 宿主对象（如 `Game`），供场景通过 `self.game` 获取工厂等资源 |

### 公共接口

| 方法 | 说明 |
|---|---|
| `register(name, scene)` | 注册场景 |
| `get(name)` | 按名称获取场景 |
| `switch(name)` | 切换场景：先 `on_exit` 当前场景，再 `on_enter` 目标场景 |
| `resize / handle_events / update / render` | 转发给当前场景 |

### 属性

`current`（当前 `Scene`）、`current_name`（当前场景名）

## 使用示例

```python
from SDLCore.scene import Scene, SceneManager
from SDLCore.ui.label import Label

class MainScene(Scene):
    SCENE_NAME = "main"
    NEXT_SCENE = "setting"

    def on_enter(self):
        if not hasattr(self, "_built"):
            label = Label((100, 100, 200, 30), text="主界面",
                          color=(0, 200, 200, 255), factory=self.game.factory)
            self.ui.root_panel.add_child(label)
            self._built = True

sm = SceneManager(game)
sm.register(MainScene.SCENE_NAME, MainScene(sm))
sm.switch(MainScene.SCENE_NAME)   # 进入主场景

# 切换场景：sm.switch("setting")
```

> 项目演示：`main.py` 注册 6 个控件测试场景（按钮 / 输入框 / 面板 / 滚动 / 网格 / 进度条），
> 它们继承游戏层 `game/scene_common.DemoScene`（提供标题/说明/页面切换按钮），
> 各场景内通过 `Button` 的 `callback=lambda: self.manager.switch(...)` 实现页面跳转。
