# ComboBox（下拉选择框控件）

**模块**：`SDLCore/ui/combobox.py`

## 概述

继承 `Widget` 的下拉选择框：头部矩形框（带边框）显示当前选中文本 + 右侧倒三角（▾）；
点击头部展开/收起下拉列表（单选 `ListBox`）。

## 关键设计：下拉浮于最上层

下拉容器**不挂载在控件自身**，而是通过 `_get_manager()` 找到 `UIManager`，
直接添加到 **`root_panel`（场景顶层）** 并设置高 `layer`（`自身 layer + 100`），
从而脱离任何容器（如 `ScrollPanel`）的裁剪，始终浮于界面最上层。
位置计算在头部正下方、宽度与头部一致；高度按 Item 数动态计算（最大 150px，超出显示滚动条）。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小（头部）** |
| `items` | `list[str]` | ✅ | — | **下拉选项** |
| `selected_index` | `int` | | `0` | 初始选中索引 |
| `on_select` | `callable` | | `None` | 选择后回调 `on_select(text, index)` |
| `factory` | `SpriteFactory` | ✅ | `None` | **TEXTURE 渲染工厂（文字渲染必需）** |
| `id` / `layer` / `layout_weight` | — | | — | 同 `Widget` |

## 交互

- 点击头部：展开/收起下拉。
- 点击下拉项：选中、收起、更新头部文本、回调 `on_select(text, index)`。
- 点击头部外部：自动收起。
- `set_enabled(False)`：禁用并收起下拉。

## 清理

- 收起时从父容器（`UIManager.root_panel`）**移除**下拉 Panel，防止泄漏与悬空渲染。
- `__del__` 兜底清理。

## 使用示例

```python
from SDLCore.ui.combobox import ComboBox

cb = ComboBox((100, 100, 180, 30), items=["红", "绿", "蓝"],
              selected_index=0,
              on_select=lambda t, i: print(f"选择: {t} ({i})"),
              factory=factory)
```

> JSON 配置（UIBuilder）：`{"type": "combobox", "id": "cbx1", "rect": [10,10,200,30],
> "items": ["A","B","C"], "selected_index": 1, "on_select": "on_sel"}`。
