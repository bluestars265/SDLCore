# -*- coding: utf-8 -*-
"""ModManager：MOD 加载系统（通用引擎层，与具体游戏无关）。

约定：
- ``mods/<mod_id>/mod.json`` 描述元数据（id / name / version / priority / depends / entry）。
- 每个 mod 可提供入口模块（如 ``main.py``），约定导出 ``register(api)``，
  由 ModManager 按依赖/优先级顺序依次调用（priority 小的先，base_game=0 最先）。
- 入口通过 ``ModAPI`` 门面注册场景、自定义控件、事件、资源路径。
- 配置型场景（JSON）经 ``ModScene`` + ``UIBuilder`` 自动加载。

不做：代码沙箱 / 热加载 / 依赖版本解析（约定为可信 mod）。
"""

import importlib.util
import json
import os

from SDLCore.scene import ModScene


class ModInfo:
    """单个 mod 的元数据与目录信息。"""

    def __init__(self, mod_dir: str, meta: dict) -> None:
        self.dir = os.path.abspath(mod_dir)
        self.id = meta["id"]
        self.name = meta.get("name", self.id)
        self.version = meta.get("version", "0.0.0")
        self.priority = meta.get("priority", 100)
        self.depends = meta.get("depends", [])
        self.entry = meta.get("entry")            # 入口模块相对路径（如 main.py）

    def resource(self, rel: str) -> str:
        """返回 mod 目录下相对路径的绝对路径。"""
        return os.path.join(self.dir, rel)


class ModAPI:
    """MOD 入口门面：mod 的 ``register(api)`` 通过它注册能力。"""

    def __init__(self, manager, info: ModInfo) -> None:
        self.manager = manager
        self.mod = info
        self.registry = manager.registry
        self.scene_manager = manager.scene_manager
        self.factory = manager.factory
        self.resources = manager.resources

    def register_component(self, type_name: str, factory) -> None:
        """注册自定义控件类型（供 JSON 场景按 type 名使用）。"""
        self.registry.register(type_name, factory)

    def register_scene(self, name: str, scene_cls) -> None:
        """注册代码型场景类（scene_cls 接收 manager 参数）。"""
        self.scene_manager.register(name, scene_cls(self.scene_manager))

    def add_scene(self, scene_id: str, title: str, file: str,
                  bindings=None) -> None:
        """注册配置型场景（file 相对 mod 目录；bindings 为事件处理器名->回调）。"""
        self.manager._config_scenes.append({
            "id": scene_id,
            "title": title,
            "file": self.mod.resource(file),
            "bindings": bindings or {},
            "mod_dir": self.mod.dir,
        })

    def bind_events(self, handlers: dict) -> None:
        """向全局事件总线注册处理器（event -> handler）。"""
        for event, handler in handlers.items():
            self.scene_manager.events.on(event, handler)

    def resource_path(self, rel: str) -> str:
        """返回 mod 资源目录下的绝对路径。"""
        return self.mod.resource(rel)

    def get_mod(self, mod_id: str) -> ModInfo:
        """访问其他 mod 的元数据。"""
        return self.manager.mods[mod_id]


class ModManager:
    """MOD 管理器：发现、依赖排序、按序调用入口、安装场景。"""

    def __init__(self, mods_dir: str | list = "mods") -> None:
        self.mods_dir = mods_dir      # str 或 list（多目录扫描，如 ["mods", "test_mods"]）
        self.mods = {}          # id -> ModInfo
        self._order = []        # 已排序加载顺序（ModInfo 列表）
        self._config_scenes = []  # 配置型场景定义
        self.registry = None
        self.factory = None
        self.resources = None
        self.scene_manager = None

    def attach_engine(self, factory, resources, scene_manager,
                      registry=None) -> None:
        """挂载引擎依赖（由启动器调用）。"""
        from SDLCore.ui.builder import ComponentRegistry
        self.factory = factory
        self.resources = resources
        self.scene_manager = scene_manager
        self.registry = registry or ComponentRegistry()

    def discover(self) -> None:
        """扫描 mods 目录（单个或多个），读取 mod.json，按 priority + depends 拓扑排序。"""
        dirs = [self.mods_dir] if isinstance(self.mods_dir, str) else self.mods_dir
        for base in dirs:
            if not os.path.isdir(base):
                print(f"警告: mods 目录不存在: {base}")
                continue
            for name in sorted(os.listdir(base)):
                d = os.path.join(base, name)
                if not os.path.isdir(d):
                    continue
                meta_path = os.path.join(d, "mod.json")
                if not os.path.exists(meta_path):
                    continue
                with open(meta_path, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                if "id" not in meta:
                    print(f"警告: mod 缺少 id 字段，已忽略: {d}")
                    continue
                self.mods[meta["id"]] = ModInfo(d, meta)
        self._order = self._topo_sort()

    def _topo_sort(self):
        """按依赖关系拓扑排序（依赖者后加载），同层按 priority 升序。"""
        result, visited, visiting = [], set(), set()

        def visit(mid):
            if mid in visited:
                return
            if mid in visiting:
                raise RuntimeError(f"mod 循环依赖: {mid}")
            visiting.add(mid)
            for dep in self.mods[mid].depends:
                if dep in self.mods:
                    visit(dep)
            visiting.discard(mid)
            visited.add(mid)
            result.append(self.mods[mid])

        for info in sorted(self.mods.values(), key=lambda m: m.priority):
            visit(info.id)
        return result

    def load_all(self) -> None:
        """按加载顺序调用各 mod 入口的 register(api)。"""
        for info in self._order:
            self._load_mod(info)

    def _load_mod(self, info: ModInfo) -> None:
        api = ModAPI(self, info)
        if info.entry:
            entry_path = info.resource(info.entry)
            if os.path.exists(entry_path):
                mod_name = f"_mod_{info.id}"
                spec = importlib.util.spec_from_file_location(mod_name, entry_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                register = getattr(module, "register", None)
                if callable(register):
                    register(api)

    def install_scenes(self) -> list:
        """为收集的配置场景设置切换链并注册到 SceneManager。返回场景定义列表。"""
        specs = self._config_scenes
        n = len(specs)
        for i, spec in enumerate(specs):
            nxt = specs[(i + 1) % n]["id"] if n > 1 else None
            scene = ModScene(
                self.scene_manager,
                spec["id"],
                spec["file"],
                bindings=spec["bindings"],
                next_scene=nxt,
                resource_resolver=lambda rel, d=spec["mod_dir"]:
                    self._resolve_mod_resource(rel, d),
                registry=self.registry,
            )
            self.scene_manager.register(spec["id"], scene)
        return specs

    def _resolve_mod_resource(self, rel: str, mod_dir: str) -> str:
        """解析场景资源路径。

        - ``@mod_id/rel``：跨 mod 引用（从指定 mod 目录解析，如素材归主 mod 时）。
        - 其余：相对当前 mod 目录。
        """
        if rel.startswith("@"):
            mod_id, _, inner = rel[1:].partition("/")
            info = self.mods.get(mod_id)
            if info is not None:
                return os.path.join(info.dir, inner)
            print(f"警告: 跨 mod 资源引用未找到 mod '{mod_id}': {rel}")
        return os.path.join(mod_dir, rel)

