# CheckBox（复选框控件）

**模块**：`SDLCore/ui/checkbox.py`

## 概述

继承 `Widget` 的复选框：方框（左边缘、垂直居中）+ 文本 `Label`（方框右侧）。
鼠标左键点击控件矩形内切换 `checked` 并调用 `callback(checked)`。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小（w 为整个控件宽度）** |
| `text` | `str` | | `""` | 方框右侧显示的文本 |
| `checked` | `bool` | | `False` | 初始选中状态 |
| `callback` | `callable` | | `None` | 点击切换后调用，接收 `checked` |
| `factory` | `SpriteFactory` | ✅ | `None` | **TEXTURE 渲染工厂（文字渲染必需）** |
| `id` / `layer` / `layout_weight` | — | | — | 同 `Widget` |

## 外观

- 未选中：灰色边框 + 白色内部。
- 选中：黑色边框 + 主题色（蓝）填充 + 白色对勾。
- 常量：`BOX_SIZE`（20）、`GAP`（6）、`COLOR_CHECKED`、`COLOR_BORDER_CHECKED` 等。

## 公共接口

- 继承 `Widget` 全部接口
- `set_text(text)`：更新文本显示
- `set_checked(checked)`：设置选中状态（不触发回调）
- `measure(constraints)`：方框 + 间距 + 文字宽（支持布局 fit_content）

## 使用示例

```python
from SDLCore.ui.checkbox import CheckBox

cb = CheckBox((100, 100, 160, 30), text="启用", factory=factory,
              callback=lambda v: print(f"选中: {v}"))
cb.set_checked(True)
cb.set_text("启用功能")
```

> JSON 配置（UIBuilder）：`{"type": "checkbox", "id": "opt1", "rect": [0,0,0,26],
> "text": "选项 A", "on_change": "on_option_changed"}`。
