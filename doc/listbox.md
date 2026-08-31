# ListBox（列表选择控件）

**模块**：`SDLCore/ui/listbox.py`

## 概述

继承 `ScrollPanel` 的列表控件：内部 `content` 使用 `VBoxLayout`，每个 Item 为 `Panel`（背景可切换）包裹 `Label`。
支持多选（`Ctrl` 切换 / `Shift` 范围选择），选中项背景高亮。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小（视口）** |
| `items` | `list[str]` | ✅ | — | **列表项文本** |
| `allow_multi_select` | `bool` | | `True` | 是否允许多选 |
| `on_selection_changed` | `callable` | | `None` | 选中变化后回调 `(items 文本列表)` |
| `factory` | `SpriteFactory` | ✅ | `None` | **TEXTURE 渲染工厂（文字渲染必需）** |
| `id` / `layer` / `layout_weight` | — | | — | 同 `Widget` |

## 交互（模拟 Ctrl/Shift）

- **单击**：选中当前点击项。
- **Ctrl + 单击**：切换当前项选中状态（不影响其他项）。
- **Shift + 单击**：选中从锚点（上次点击项）到当前项的范围。
- 单选模式（`allow_multi_select=False`）：忽略 Ctrl/Shift，单击即单选。
- 选中项背景高亮（半透明蓝），未选中透明。
- 滚轮滚动由父类 `ScrollPanel` 提供；Item 点击消费事件不冒泡误触。

## 接口

| 方法 | 说明 |
|---|---|
| `set_items(new_items)` | 刷新列表（清空选中） |
| `get_selected()` | 返回选中文本列表 |
| `get_selected_indices()` | 返回选中索引列表 |

## 使用示例

```python
from SDLCore.ui.listbox import ListBox

lb = ListBox((50, 50, 200, 200), items=["苹果", "香蕉", "橙子", "葡萄"],
             allow_multi_select=True,
             on_selection_changed=lambda texts: print(f"选中: {texts}"),
             factory=factory)
lb.set_items(["一", "二", "三"])     # 刷新
print(lb.get_selected())
```

> JSON 配置（UIBuilder）：`{"type": "listbox", "id": "lb1", "rect": [10,10,200,180],
> "items": ["A","B","C"], "on_selection_changed": "on_sel"}`。
