# -*- coding: utf-8 -*-
"""ResourceManager：全局纹理资源管理器（通用引擎层，与具体游戏无关）。

- 统一缓存外部图片纹理（TextureSprite），避免重复加载。
- ``get(path)``：同步获取（缓存命中直接返回，否则立即加载并缓存）。
- ``load_async(path)``：后台线程解码图片为 SDL_Surface；
  主线程调用 ``process_pending()`` 将其转为纹理并缓存。

格式支持：经 SDL_image（``IMG_Load``）解码，支持 PNG / JPG / BMP / GIF / TGA 以及
**SVG**（SDL_image 2.8+ 内置 SVG 矢量光栅化，pysdl2-dll 2.32.10 实测可用）。
组件（``ImageButton`` / ``ProgressBar`` / ``ScrollPanel`` 等）传入 ``.svg`` 路径
即可直接加载渲染；SVG 按原尺寸光栅化，渲染时由组件拉伸到目标矩形。

注意：SDL 纹理必须在主线程（渲染线程）创建，因此异步加载只负责后台解码，
纹理创建统一由主线程 ``process_pending()`` 完成。
"""

import threading

import sdl2
import sdl2.ext
import sdl2.sdlimage


class ResourceManager:
    """纹理资源管理器（线程安全）。"""

    def __init__(self, factory=None):
        self._factory = factory
        self._cache = {}       # path -> TextureSprite
        self._surfaces = {}    # path -> SDL_Surface（后台加载完成，待主线程转纹理）
        self._loading = set()  # path 正在后台加载
        self._failed = set()   # path 加载失败（不再重试）
        self._lock = threading.Lock()

    def set_factory(self, factory) -> None:
        """设置 TEXTURE 渲染工厂。"""
        self._factory = factory

    @property
    def factory(self):
        return self._factory

    def has(self, path: str) -> bool:
        with self._lock:
            return path in self._cache

    def is_loading(self, path: str) -> bool:
        """该资源是否正在后台解码（用于加载进度统计）。"""
        with self._lock:
            return path in self._loading

    def failed(self, path: str) -> bool:
        """该资源是否已确定加载失败（不再重试）。"""
        with self._lock:
            return path in self._failed

    def get(self, path: str):
        """同步获取纹理：缓存命中直接返回，否则立即加载并缓存。"""
        with self._lock:
            if path in self._cache:
                return self._cache[path]
        if self._factory is None:
            raise RuntimeError("ResourceManager 未设置渲染工厂")
        sprite = self._factory.from_image(path)
        with self._lock:
            self._cache[path] = sprite
        return sprite

    def load_async(self, path: str) -> None:
        """异步加载：后台线程解码图片 surface，主线程 process_pending 转为纹理。"""
        with self._lock:
            if path in self._cache or path in self._loading or path in self._failed:
                return
            self._loading.add(path)
        threading.Thread(target=self._load_surface, args=(path,), daemon=True).start()

    def _load_surface(self, path: str) -> None:
        try:
            ptr = sdl2.sdlimage.IMG_Load(path.encode("utf-8"))
            if not ptr:
                raise RuntimeError(sdl2.SDL_GetError() or "IMG_Load 失败")
            with self._lock:
                self._surfaces[path] = ptr.contents
        except Exception as exc:  # noqa: BLE001
            print(f"警告: 异步加载图片失败 {path}: {exc}")
            with self._lock:
                self._failed.add(path)
        finally:
            with self._lock:
                self._loading.discard(path)

    def process_pending(self) -> None:
        """主线程每帧调用：将后台加载完成的 surface 转为纹理并缓存。"""
        if self._factory is None:
            return
        with self._lock:
            items = list(self._surfaces.items())
        for path, surface in items:
            try:
                sprite = self._factory.from_surface(surface, free=True)
                with self._lock:
                    self._cache[path] = sprite
                    del self._surfaces[path]
            except Exception as exc:  # noqa: BLE001
                print(f"警告: 纹理创建失败 {path}: {exc}")
                with self._lock:
                    del self._surfaces[path]


# 全局默认资源管理器（单渲染器应用共享）
resources = ResourceManager()
