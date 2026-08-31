# InputBox（文本输入框控件）

**模块**：`SDLCore/ui/inputbox.py`

## 概述

支持**系统 IME（中文/日文输入法）**的文本输入框：
- 点击框内激活（`SDL_StartTextInput` 启用 IME），点击框外失焦。
- `SDL_TEXTINPUT` 事件：输入法上屏文本插入光标处；`SDL_TEXTEDITING`：组合文本（拼音）灰色半透明显示。
- 按键：`Backspace`/`Delete` 删除、`←`/`→` 移动光标、`Home`/`End` 行首/行尾跳转、`Enter` 触发 `on_submit(text)`。
- **标准编辑**：`Ctrl+A` 全选、`Ctrl+C`/`Ctrl+X`/`Ctrl+V` 复制/剪切/粘贴（系统剪贴板）、
  `Shift+←/→` 与 `Shift+Home/End` 扩展选区、鼠标左键拖拽选择、输入时替换选区（半透明蓝高亮）。
- 文本过长时**横向滚动**（光标跟随），光标闪烁，渲染裁剪在输入框内。

## 构造参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|---|---|---|---|---|
| `rect` | `tuple (x, y, w, h)` | ✅ | — | **位置与大小** |
| `font_path` | `str` | | `None` | 字体文件路径；默认从 `resource/fonts/` 查找（回退系统字体） |
| `font_size` | `str` | | `"18px"` | 字号（如 `"18px"`、`"14pt"`） |
| `on_submit` | `callable` | | `None` | 回车回调，接收参数 `text` |
| `parent` / `visible` / `enabled` | — | | — | 同 `Widget` |
| `factory` | `SpriteFactory` | ✅ | `None` | **TEXTURE 渲染工厂**（文字渲染必需） |

## 公共接口

- 继承 `Widget` 全部接口
- `set_factory(factory)`：设置文字渲染工厂
- `set_text(text)`：设置输入框内容，光标移到末尾
- `update(delta_time)`：光标闪烁 + IME 候选窗口定位（由 `UIManager.update` 自动驱动）

## 重要说明

1. **IME 原生 UI**：需在**创建窗口之前**设置 hint，否则系统输入法的候选词/组合条不显示：
   ```python
   sdl2.SDL_SetHint(b"SDL_IME_SHOW_UI", b"1")
   ```
2. `update` 每帧调用由 `UIManager.update(delta_time)`（或场景）自动完成，无需手动调用。

## 使用示例

```python
from SDLCore.ui.inputbox import InputBox

box = InputBox(
    (100, 100, 240, 40),
    font_size="18px",
    on_submit=lambda t: print(f"输入内容: {t}"),
    factory=factory,
)
box.set_text("预设内容")
```
