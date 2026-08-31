# 渲染性能优化

## 矩形合批（BatchedRenderer）

**模块**：`SDLCore/ui/batcher.py`

`UIManager.render` 渲染整棵 UI 树时，用 `BatchedRenderer` 包装渲染器：

- **不透明纯色矩形**（`fill` / `draw_rect`）被收集为绘制命令；
- 按 `(类型, 颜色)` **全量分组**，同色矩形用 `SDL_RenderFillRects` / `SDL_RenderDrawRects`
  **一次提交多个**（大幅减少 Draw Call：如 6 个同色按钮的填充从 6 次降为 1 次）；
- 绘制顺序按各组**首次出现序号**保持（z 顺序正确）。
- **半透明矩形**与**裁剪区域内矩形**保持逐次绘制（保证 alpha 混合与裁剪正确）；
  `copy`（纹理）前自动 flush 已收集命令（保证 z 顺序）。

裁剪感知通过 `SDLCore.ui.set_render_clip(renderer, rect)` 钩子实现
（`BatchedRenderer` 与原生 `Renderer` 均兼容）；`InputBox` / `ScrollPanel` 已改用该钩子。

## 脏标记（Dirty Flag）

- `Widget` 维护 `_dirty` 重绘标记与 `mark_dirty()`。
- 状态 / 尺寸 / 可见性变化时自动置脏：`set_rect` / `set_visible` / `set_enabled`，
  以及各控件状态 setter（`set_checked` / `set_selected` / `set_value` / `set_text` 等）。
- 文字控件（`Label` / `InputBox` / `Button` fit_content）的**纹理已按 `(text, color)` 缓存**，
  内容未变时直接复用纹理，不重复生成（`FontTTF.render_text` 仅按需调用）。

## 适用说明

- 合批主要收益来自**大量同色不透明矩形**（按钮列表、进度条、列表项背景）。
- 文字 / 图片（`copy`）在 SDL2 下无法跨精灵合并（无批量复制 API），其优化依赖纹理缓存（已实现）。
- 复杂静态 UI 可进一步结合容器级离屏缓存（RenderTarget）扩展。
