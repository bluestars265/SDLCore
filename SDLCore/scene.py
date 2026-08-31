# -*- coding: utf-8 -*-
"""场景系统：通用引擎层，与具体游戏无关。

- ``EventBus``：轻量事件总线（发布 / 订阅），用于场景间或控件间通信。
- ``Scene``：场景基类。每个场景拥有独立的 UI 树（``UIManager``），
  通过 ``on_enter`` / ``on_exit`` / ``on_resize`` 管理生命周期。
- ``SceneManager``：注册与切换场景，并把 resize / 事件 / 更新 / 渲染
  转发给当前场景；提供 ``shared_data``（共享数据模型）与 ``events``（事件总线）
  作为场景间通信机制。
"""

import sdl2

from SDLCore.ui.manager import UIManager


class EventBus:
    """轻量事件总线：支持按事件名订阅 / 取消订阅 / 发布。"""

    def __init__(self) -> None:
        self._handlers = {}  # event -> [handler, ...]

    def on(self, event: str, handler) -> None:
        """订阅事件。"""
        self._handlers.setdefault(event, []).append(handler)

    def off(self, event: str, handler) -> None:
        """取消订阅事件。"""
        handlers = self._handlers.get(event)
        if handlers and handler in handlers:
            handlers.remove(handler)
            if not handlers:
                del self._handlers[event]

    def emit(self, event: str, *args, **kwargs) -> None:
        """发布事件，同步调用所有已订阅的处理器。"""
        for handler in list(self._handlers.get(event, [])):
            handler(*args, **kwargs)

    def clear(self, event: str | None = None) -> None:
        """清空全部或指定事件的订阅。"""
        if event is None:
            self._handlers.clear()
        else:
            self._handlers.pop(event, None)

    def has_listeners(self, event: str) -> bool:
        return bool(self._handlers.get(event))


class Scene:
    """场景基类：管理自身的 UI 树与生命周期钩子。"""

    def __init__(self, manager):
        self.manager = manager        # SceneManager 引用
        self.game = manager.game      # 持有 window / factory 等资源的 Game 引用
        self.ui = UIManager()

    # ---- 场景间通信便捷访问 ----

    @property
    def shared_data(self):
        """场景间共享数据模型（dict）。"""
        return self.manager.shared_data

    @property
    def events(self):
        """场景间事件总线。"""
        return self.manager.events

    # ---- 生命周期 ----

    def on_enter(self) -> None:
        """进入场景时调用（子类可重写，例如首次进入时构建 UI）。"""

    def on_exit(self) -> None:
        """离开场景时调用：关闭系统输入法并清空输入焦点。"""
        sdl2.SDL_StopTextInput()
        self.ui.set_focus(None)

    # ---- 转发 ----

    def resize(self, width: int, height: int) -> None:
        """更新本场景根面板铺满全屏，并刷新子控件绝对坐标。"""
        self.ui.resize(width, height)
        self.on_resize(width, height)

    def on_resize(self, width: int, height: int) -> None:
        """窗口尺寸变化钩子（子类可按需重写，例如重新计算布局）。"""
        pass

    def handle_events(self, events) -> None:
        self.ui.handle_events(events)

    def update(self, delta_time: float) -> None:
        self.ui.update(delta_time)

    def render(self, renderer) -> None:
        self.ui.render(renderer)

    def get_widget(self, widget_id):
        """在当前场景 UI 树中按 id 查找控件。"""
        return self.ui.find_by_id(widget_id)


class SceneManager:
    """场景管理器：注册、切换场景，并向当前场景转发各帧调用。"""
    def __init__(self, game=None):
        self.game = game
        self.shared_data = {}   # 场景间共享数据模型（可跨场景读写）
        self.events = EventBus()  # 场景间事件总线（on/off/emit）
        self._scenes = {}
        self._current_name = None

    def register(self, name: str, scene: Scene) -> None:
        """注册一个场景（使用字符串名标识）。"""
        self._scenes[name] = scene

    def get(self, name: str) -> Scene:
        return self._scenes[name]

    def names(self) -> list[str]:
        """返回所有已注册场景名。"""
        return list(self._scenes.keys())

    def switch(self, name: str) -> None:
        """切换到指定场景：先退出当前场景，再进入目标场景。"""
        if name not in self._scenes:
            raise KeyError("未注册的场景: {0}".format(name))
        if self._current_name is not None:
            self._scenes[self._current_name].on_exit()
        self._current_name = name
        self._scenes[name].on_enter()

    @property
    def current(self) -> Scene | None:
        return self._scenes[self._current_name] if self._current_name else None

    @property
    def current_name(self) -> str | None:
        return self._current_name

    def resize(self, width: int, height: int) -> None:
        if self.current is not None:
            self.current.resize(width, height)

    def handle_events(self, events) -> None:
        if self.current is not None:
            self.current.handle_events(events)

    def update(self, delta_time: float) -> None:
        if self.current is not None:
            self.current.update(delta_time)

    def render(self, renderer) -> None:
        if self.current is not None:
            self.current.render(renderer)


class ModScene(Scene):
    """配置驱动场景（通用引擎层）：从 JSON 场景包构建 UI，并提供场景切换栏。

    参数：
    - ``scene_file``：场景 JSON 路径（UIBuilder.build_file）。
    - ``bindings``：事件处理器名 -> 代码回调。
    - ``next_scene``：切换按钮指向的下一个场景名（None 则不显示切换栏）。
    - ``resource_resolver``：把配置中的相对资源路径映射到 mod 资源目录。
    """

    def __init__(self, manager, scene_id: str, scene_file: str,
                 bindings=None, next_scene=None, resource_resolver=None,
                 registry=None) -> None:
        super().__init__(manager)
        self.scene_id = scene_id
        self.scene_file = scene_file
        self.bindings = bindings or {}
        self.next_scene = next_scene
        self.resource_resolver = resource_resolver
        self.registry = registry  # 共享控件注册表（含 mod 注册的自定义控件）
        self.TITLE = scene_id
        self._built = False
        self.switch_btn = None

    def on_enter(self) -> None:
        if not self._built:
            self._build_ui()
            self._built = True

    def _build_ui(self) -> None:
        from SDLCore.ui.builder import UIBuilder
        from SDLCore.ui.panel import Panel
        from SDLCore.ui.label import Label
        from SDLCore.ui.button import Button

        builder = UIBuilder(
            factory=self.game.factory,
            registry=self.registry,
            resource_resolver=self.resource_resolver,
        )
        root = builder.build_file(self.scene_file, bindings=self.bindings)
        self.ui.root_panel.add_child(root)

        # 底部场景切换栏
        if self.next_scene:
            width, height = self.game.window.size
            nxt_title = getattr(
                self.manager.get(self.next_scene), "TITLE", self.next_scene
            )
            bar = Panel((width // 2 - 110, height - 84, 220, 66),
                        color=(0, 0, 0, 0))
            hint = Label(
                (0, 2, 220, 22), text=f"点击下方按钮 → {nxt_title}",
                color=(255, 255, 255, 255), factory=self.game.factory,
            )
            btn = Button((30, 28, 160, 34))
            btn.callback = lambda: self.manager.switch(self.next_scene)
            bar.add_child(hint)
            bar.add_child(btn)
            self.ui.root_panel.add_child(bar)
            self.switch_btn = btn
