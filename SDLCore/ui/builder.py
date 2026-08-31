# -*- coding: utf-8 -*-
"""UIBuilder：声明式（配置驱动）UI 构建器（通用引擎层，与具体游戏无关）。

综合方案：
- **快速搭建**：JSON / dict 描述控件树（类型、位置、颜色、资源路径、布局、事件处理器名、
  ``id``、``layer``），一键递归构建。
- **高自由度**：
  1. 事件处理器不在配置中实现，通过 ``bindings`` 由代码注入；
  2. 控件类型由 ``ComponentRegistry`` 管理，可注册自定义控件工厂扩展任意类型。
- **组件复用**：``$ref`` 外部引用（相对场景目录），可用 ``override`` 覆盖属性。
- **控件管理**：配置中的 ``id`` 写入控件并登记到 ``builder.by_id``；``layer`` 写入控件图层。
"""

import json
import os

from SDLCore.ui.panel import Panel
from SDLCore.ui.button import Button
from SDLCore.ui.checkbox import CheckBox
from SDLCore.ui.radiogroup import RadioGroup
from SDLCore.ui.slider import Slider
from SDLCore.ui.listbox import ListBox
from SDLCore.ui.combobox import ComboBox
from SDLCore.ui.imagebutton import ImageButton
from SDLCore.ui.label import Label
from SDLCore.ui.inputbox import InputBox
from SDLCore.ui.scrollpanel import ScrollPanel
from SDLCore.ui.progressbar import ProgressBar
from SDLCore.ui.layout import GridLayout as GridLayoutLayout
from SDLCore.ui.layout import VBoxLayout, HBoxLayout


class ComponentRegistry:
    """控件类型注册表：类型名 -> 工厂函数（props, ctx）-> 控件。"""

    def __init__(self) -> None:
        self._factories = {}
        self._register_builtins()

    def register(self, type_name: str, factory) -> None:
        """注册自定义控件类型工厂（高自由度扩展）。"""
        self._factories[type_name] = factory

    def create(self, type_name: str, props, ctx):
        if type_name not in self._factories:
            raise KeyError(f"未注册的控件类型: {type_name}")
        return self._factories[type_name](props, ctx)

    def _register_builtins(self) -> None:
        self.register("button", _build_button)
        self.register("checkbox", _build_checkbox)
        self.register("radio_group", _build_radio_group)
        self.register("slider", _build_slider)
        self.register("listbox", _build_listbox)
        self.register("combobox", _build_combobox)
        self.register("image_button", _build_image_button)
        self.register("label", _build_label)
        self.register("inputbox", _build_inputbox)
        self.register("panel", _build_panel)
        self.register("scroll_panel", _build_scroll_panel)
        self.register("progress_bar", _build_progress_bar)


class BuildContext:
    """构建上下文：渲染工厂、事件绑定、控件注册表、场景目录。"""

    def __init__(self, factory, bindings, registry: ComponentRegistry,
                 scene_dir=None, resource_resolver=None) -> None:
        self.factory = factory
        self.bindings = bindings or {}
        self.registry = registry
        self.scene_dir = scene_dir  # 用于解析 $ref 相对路径
        # 资源路径解析器（mod 场景把相对路径映射到 mod 资源目录）
        self._resource_resolver = resource_resolver

    def resolve(self, name):
        """按名称解析事件处理器（从 bindings 中查找）。"""
        if not name:
            return None
        handler = self.bindings.get(name)
        if handler is None:
            print(f"警告: 未绑定事件处理器 '{name}'")
        return handler

    def resolve_resource(self, path):
        """解析资源路径；未配置解析器时原样返回。"""
        if not path or self._resource_resolver is None:
            return path
        return self._resource_resolver(path)


class UIBuilder:
    """解析配置 dict / JSON 文件，递归构建控件树。"""

    def __init__(self, factory=None, registry: ComponentRegistry | None = None,
                 resource_resolver=None) -> None:
        self.factory = factory
        self.registry = registry or ComponentRegistry()
        self.resource_resolver = resource_resolver  # 相对路径 -> 绝对路径
        self.by_id = {}  # id -> widget（配置中声明了 id 的控件）

    def build(self, spec, bindings=None):
        """从配置 dict 构建控件树，返回根控件。"""
        ctx = BuildContext(self.factory, bindings, self.registry,
                           resource_resolver=self.resource_resolver)
        return self._build_node(spec, ctx, None)

    def build_file(self, path, bindings=None):
        """从 JSON 文件构建控件树（支持相对 $ref 引用）。"""
        scene_dir = os.path.dirname(os.path.abspath(path))
        with open(path, "r", encoding="utf-8") as fh:
            spec = json.load(fh)
        ctx = BuildContext(self.factory, bindings, self.registry,
                           scene_dir=scene_dir,
                           resource_resolver=self.resource_resolver)
        return self._build_node(spec, ctx, None)

    def _resolve_ref(self, spec, ctx):
        """解析 $ref：读取外部组件 json，合并 override 覆盖。"""
        ref_path = os.path.join(ctx.scene_dir, spec["$ref"])
        with open(ref_path, "r", encoding="utf-8") as fh:
            resolved = json.load(fh)
        override = spec.get("override")
        if isinstance(override, dict):
            resolved = dict(resolved)
            resolved.update(override)
        return resolved

    def _build_node(self, spec, ctx, parent):
        if "$ref" in spec:
            spec = self._resolve_ref(spec, ctx)
        widget = ctx.registry.create(spec.get("type", "panel"), spec, ctx)
        # id / layer：基类属性，构造后赋值
        if "id" in spec:
            widget.id = spec["id"]
            self.by_id[widget.id] = widget
        if "layer" in spec:
            widget.layer = int(spec["layer"])
        if "weight" in spec:
            widget.layout_weight = int(spec["weight"])
        if "opacity" in spec:
            widget.set_opacity(float(spec["opacity"]))
        if parent is not None:
            parent.add_child(widget)
        for child in spec.get("children", []):
            self._build_node(child, ctx, widget)
        return widget


# ---- 内置控件工厂 ----


def _as_rect(props):
    r = props.get("rect")
    return tuple(r) if r else (0, 0, 0, 0)


def _build_button(props, ctx):
    return Button(
        _as_rect(props),
        text=props.get("text", ""),
        callback=ctx.resolve(props.get("on_click")),
    )


def _build_checkbox(props, ctx):
    return CheckBox(
        _as_rect(props),
        text=props.get("text", ""),
        checked=bool(props.get("checked", False)),
        callback=ctx.resolve(props.get("on_change")),
        factory=ctx.factory,
    )


def _build_radio_group(props, ctx):
    return RadioGroup(
        _as_rect(props),
        options=props.get("options", []),
        selected_index=props.get("selected_index", 0),
        on_select=ctx.resolve(props.get("on_select")),
        factory=ctx.factory,
        horizontal=bool(props.get("horizontal", False)),
    )


def _build_slider(props, ctx):
    return Slider(
        _as_rect(props),
        min_val=props.get("min", 0.0),
        max_val=props.get("max", 100.0),
        value=props.get("value", 0.0),
        step=props.get("step", 1.0),
        on_value_changed=ctx.resolve(props.get("on_value_changed")),
        factory=ctx.factory,
    )


def _build_listbox(props, ctx):
    return ListBox(
        _as_rect(props),
        items=props.get("items", []),
        allow_multi_select=bool(props.get("allow_multi_select", True)),
        on_selection_changed=ctx.resolve(props.get("on_selection_changed")),
        factory=ctx.factory,
    )


def _build_combobox(props, ctx):
    return ComboBox(
        _as_rect(props),
        items=props.get("items", []),
        selected_index=props.get("selected_index", 0),
        on_select=ctx.resolve(props.get("on_select")),
        factory=ctx.factory,
    )


def _build_image_button(props, ctx):
    return ImageButton(
        _as_rect(props),
        image_normal=ctx.resolve_resource(props.get("image_normal")),
        image_hover=ctx.resolve_resource(props.get("image_hover")),
        image_pressed=ctx.resolve_resource(props.get("image_pressed")),
        text=props.get("text", ""),
        text_color=tuple(props.get("text_color", (255, 255, 255, 255))),
        callback=ctx.resolve(props.get("on_click")),
        factory=ctx.factory,
    )


def _build_label(props, ctx):
    return Label(
        _as_rect(props),
        text=props.get("text", ""),
        color=tuple(props.get("color", (255, 255, 255, 255))),
        font_size=props.get("font_size", "18px"),
        factory=ctx.factory,
    )


def _build_inputbox(props, ctx):
    return InputBox(
        _as_rect(props),
        font_size=props.get("font_size", "18px"),
        on_submit=ctx.resolve(props.get("on_submit")),
        factory=ctx.factory,
    )


def _build_layout(props):
    if not props:
        return None
    kind = props.get("type", "vbox")
    if kind == "grid":
        return GridLayoutLayout(
            cols=props.get("cols", 1),
            cell_width=props.get("cell_width", 0),
            cell_height=props.get("cell_height", 0),
            h_spacing=props.get("h_spacing", 5),
            v_spacing=props.get("v_spacing", 5),
            padding=tuple(props.get("padding", (5, 5, 5, 5))),
        )
    if kind == "hbox":
        return HBoxLayout(
            spacing=props.get("spacing", 5),
            padding=tuple(props.get("padding", (0, 0, 0, 0))),
            align=props.get("align", "stretch"),
        )
    return VBoxLayout(
        spacing=props.get("spacing", 5),
        padding=tuple(props.get("padding", (0, 0, 0, 0))),
        align=props.get("align", "stretch"),
    )


def _build_panel(props, ctx):
    return Panel(
        _as_rect(props),
        color=tuple(props.get("color", Panel.DEFAULT_BG_COLOR)),
        layout=_build_layout(props.get("layout")),
    )


def _build_scroll_panel(props, ctx):
    cs = props.get("content_size")
    return ScrollPanel(
        _as_rect(props),
        content_size=tuple(cs) if cs else None,
        scroll_speed=props.get("scroll_speed", 30.0),
    )


def _build_progress_bar(props, ctx):
    return ProgressBar(
        _as_rect(props),
        min=props.get("min", 0.0),
        max=props.get("max", 100.0),
        value=props.get("value", 0.0),
        bg_color=tuple(props.get("bg_color", (40, 40, 40, 255))),
        fill_color=tuple(props.get("fill_color", (0, 200, 80, 255))),
        border_color=tuple(props.get("border_color", (80, 80, 80, 255))),
        fill_image=ctx.resolve_resource(props.get("fill_image")),
        indicator_image=ctx.resolve_resource(props.get("indicator_image")),
        factory=ctx.factory,
    )
