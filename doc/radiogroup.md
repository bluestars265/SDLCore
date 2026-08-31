# RadioGroup（单选组控件）

**模块**：`SDLCore/ui/radiogroup.py`

## 概述

继承 `Panel` 的单选组：内部使用 `VBoxLayout` / `HBoxLayout` 垂直或水平排列 `_RadioButton`。
选项为圆形单点：未选中**空心圆**、选中**实心圆**（主题色 + 内部白点），点击时向组报告自身索引。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `options` | `list[str]` | ✅ | — | **选项文本列表** |
| `selected_index` | `int` | | `0` | 初始选中项索引 |
| `on_select` | `callable` | | `None` | 点击选中后回调 `on_select(index, text)` |
| `factory` | `SpriteFactory` | ✅ | `None` | **TEXTURE 渲染工厂（文字渲染必需）** |
| `horizontal` | `bool` | | `False` | `True` 用 `HBoxLayout` 水平排列 |
| `id` / `layer` / `layout_weight` | — | | — | 同 `Widget` |

## 核心交互

- 点击某个 `_RadioButton` → 组**遍历子项**取消旧选中、选中当前，并调用 `on_select(index, text)`。
- `set_selected(index)`：外部程序主动切换（**不触发回调**）。
- `get_selected()`：返回 `(index, text)`。

## 内部类 `_RadioButton`

- 继承 `Widget`；外观：圆形（空心/实心）+ 右侧文本 `Label`。
- `set_checked(checked)` 更新选中外观。
- 点击调用 `group.select(self.index)`。

## 使用示例

```python
from SDLCore.ui.radiogroup import RadioGroup

rg = RadioGroup(
    (100, 100, 200, 120),
    options=["红", "绿", "蓝"],
    selected_index=0,
    on_select=lambda i, t: print(f"选中: {i} - {t}"),
    factory=factory,
)
rg.set_selected(2)   # 外部切换（不回调）
```

> JSON 配置（UIBuilder）：`{"type": "radio_group", "id": "rg1", "rect": [0,0,0,110],
> "options": ["A","B","C"], "selected_index": 1, "on_select": "on_sel"}`。
