# LogCapture（命令行输出捕获）

**模块**：`SDLCore/logcapture.py`

## 概述

捕获 Python `sys.stdout` 输出的日志采集器：替换 stdout 后，
**实时转发**到原 stdout（终端仍可见），并**线程安全**收集最近若干行
（后台线程的 `print` 也能捕获）。供加载界面等日志面板读取显示。

## 公共接口

| 方法 | 说明 |
|---|---|
| `recent(n)` | 返回最近 n 行日志 |
| `install()` | 替换 `sys.stdout` 为捕获器 |
| `restore()` | 恢复原始 stdout |

## 使用示例

```python
from SDLCore.logcapture import LogCapture

cap = LogCapture(sys.stdout)   # 记录原始 stdout
cap.install()                  # 开始捕获（print 同时转发终端）

# ... 业务打印 ...
lines = cap.recent(8)          # 界面显示最近 8 行

# cap.restore()                # 需要时恢复原始 stdout
```

> 线程安全：内部使用锁保护，后台线程的 `print` 也可安全捕获。
