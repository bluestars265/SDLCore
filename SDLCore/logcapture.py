# -*- coding: utf-8 -*-
"""LogCapture：捕获 Python 命令行输出（通用引擎层工具）。

- 替换 ``sys.stdout``，**实时转发**到原 stdout（终端仍可见）；
- **线程安全**收集最近若干行（后台线程的 print 也能捕获）；
- 供加载界面等日志面板读取显示（``recent(n)``）。
"""

import sys
import threading


class LogCapture:
    """捕获 stdout 输出的日志采集器。"""

    MAX_LINES = 200

    def __init__(self, original):
        self._orig = original
        self._lines = []
        self._lock = threading.Lock()

    # ---- stdout 接口 ----

    def write(self, text: str) -> None:
        try:
            self._orig.write(text)
        except Exception:  # noqa: BLE001
            pass
        try:
            with self._lock:
                for chunk in text.split("\n"):
                    self._lines.append(chunk.rstrip("\r"))
                if len(self._lines) > self.MAX_LINES:
                    del self._lines[:len(self._lines) - self.MAX_LINES]
        except Exception:  # noqa: BLE001
            pass

    def flush(self) -> None:
        try:
            self._orig.flush()
        except Exception:  # noqa: BLE001
            pass

    # ---- 读取 / 安装 ----

    def recent(self, n: int) -> list:
        """返回最近 n 行日志。"""
        with self._lock:
            return list(self._lines[-n:])

    def install(self) -> None:
        """替换 sys.stdout 为捕获器。"""
        sys.stdout = self

    def restore(self) -> None:
        """恢复原始 stdout。"""
        sys.stdout = self._orig
