"""
ClawSave Client - 游戏路径库管理器

从云端拉取游戏路径库，支持本地缓存和模糊搜索。
"""

import os
import json
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from logging import getLogger

from .file_handler import expand_path

if TYPE_CHECKING:
    from .webdav_client import WebDAVClient

logger = getLogger(__name__)

# 数据目录：项目根目录下的 data/ 文件夹
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
LIBRARY_CACHE_FILE = CACHE_DIR / "games_library.json"
LIBRARY_META_FILE = CACHE_DIR / "library_meta.json"

# 云端路径库路径
LIBRARY_REMOTE_PATH = "/ClawSave/_system/games_library.json"


class LibraryManager:
    """游戏路径库管理器"""

    def __init__(self):
        """初始化路径库管理器"""
        self._library: List[Dict[str, Any]] = []
        self._loaded = False
        self._last_update: Optional[datetime] = None

        # 确保缓存目录存在
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def library(self) -> List[Dict[str, Any]]:
        """获取游戏库列表"""
        return self._library

    @property
    def is_loaded(self) -> bool:
        """是否已加载"""
        return self._loaded

    @property
    def count(self) -> int:
        """游戏数量"""
        return len(self._library)

    def load(self, client: Optional['WebDAVClient'] = None, use_cache: bool = True) -> bool:
        """
        加载游戏路径库。

        优先从云端加载，失败则使用本地缓存。

        Args:
            client: WebDAV 客户端（用于从云端加载）
            use_cache: 是否使用缓存作为兜底

        Returns:
            True 如果加载成功
        """
        # 尝试从云端加载
        if client:
            try:
                data = client.download_json(LIBRARY_REMOTE_PATH, timeout=5)
                if data:
                    if isinstance(data, list):
                        self._library = data
                    elif isinstance(data, dict) and 'games' in data:
                        self._library = data['games']
                    else:
                        self._library = []

                    self._loaded = True
                    self._last_update = datetime.now()

                    # 保存到缓存
                    self._save_cache()
                    self._save_meta()

                    logger.info(f"从云端加载游戏库成功，共 {len(self._library)} 个游戏")
                    return True
            except Exception as e:
                logger.warning(f"从云端加载游戏库失败: {e}")

        # 使用本地缓存
        if use_cache:
            if self._load_cache():
                logger.info(f"从缓存加载游戏库成功，共 {len(self._library)} 个游戏")
                return True

        logger.warning("无法加载游戏路径库")
        return False

    def _load_cache(self) -> bool:
        """从缓存加载"""
        try:
            if LIBRARY_CACHE_FILE.exists():
                with open(LIBRARY_CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._library = data
                    elif isinstance(data, dict) and 'games' in data:
                        self._library = data['games']
                    else:
                        self._library = []

                self._loaded = True

                # 加载元数据
                if LIBRARY_META_FILE.exists():
                    with open(LIBRARY_META_FILE, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        if meta.get('last_update'):
                            self._last_update = datetime.fromisoformat(meta['last_update'])

                return True
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")

        return False

    def _save_cache(self):
        """保存到缓存"""
        try:
            with open(LIBRARY_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._library, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def _save_meta(self):
        """保存元数据"""
        try:
            meta = {
                'last_update': self._last_update.isoformat() if self._last_update else None
            }
            with open(LIBRARY_META_FILE, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存元数据失败: {e}")

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        模糊搜索游戏。

        Args:
            query: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            匹配的游戏列表
        """
        if not self._loaded:
            return []

        query_lower = query.lower()
        results: List[tuple] = []

        for game in self._library:
            score = 0
            name = game.get('name', '').lower()
            game_id = game.get('id', '').lower()

            # 完全匹配
            if query_lower == name:
                score = 100
            # 开头匹配
            elif name.startswith(query_lower):
                score = 80
            # 包含匹配
            elif query_lower in name:
                score = 60
            # ID 匹配
            elif query_lower in game_id:
                score = 40

            if score > 0:
                results.append((score, game))

        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)

        return [game for _, game in results[:limit]]

    def get_platform_path(self, game: Dict[str, Any]) -> Optional[str]:
        """
        获取当前平台的游戏路径。

        Args:
            game: 游戏信息字典

        Returns:
            平台对应的路径，不存在返回 None
        """
        paths = game.get('paths', {})
        system = platform.system().lower()

        # 平台映射
        platform_key = {
            'windows': 'windows',
            'darwin': 'macos',
            'linux': 'linux'
        }.get(system)

        if platform_key and platform_key in paths:
            return paths[platform_key]

        return None

    def get_expanded_path(self, game: Dict[str, Any]) -> Optional[str]:
        """
        获取展开后的游戏路径（解析环境变量）。

        Args:
            game: 游戏信息字典

        Returns:
            展开后的路径，不存在返回 None
        """
        path = self.get_platform_path(game)
        if path:
            return expand_path(path)
        return None

    def get_by_id(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取游戏信息。

        Args:
            game_id: 游戏 ID

        Returns:
            游戏信息，不存在返回 None
        """
        for game in self._library:
            if game.get('id') == game_id:
                return game
        return None


# 全局实例
_library_manager: Optional[LibraryManager] = None


def get_library_manager() -> LibraryManager:
    """获取全局路径库管理器实例"""
    global _library_manager
    if _library_manager is None:
        _library_manager = LibraryManager()
    return _library_manager
