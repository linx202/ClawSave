"""
ClawSave Client - 配置管理

负责本地 config.json 的读写操作，包括游戏配置的 CRUD 和唯一性校验。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# 默认配置文件路径
DEFAULT_CONFIG_DIR = Path.home() / ".clawsave"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"

# 配置版本
CONFIG_VERSION = "1.0"


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器。

        Args:
            config_path: 配置文件路径，默认 ~/.clawsave/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = DEFAULT_CONFIG_PATH

        self._config: dict = {}
        self._ensure_config_exists()

    def _ensure_config_exists(self) -> None:
        """确保配置文件和目录存在。"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self._config = self._create_default_config()
            self.save()
        else:
            self.load()

    def _create_default_config(self) -> dict:
        """创建默认配置结构。"""
        return {
            "config_version": CONFIG_VERSION,
            "user": {
                "username": "",
                "webdav_url": "",
                "webdav_pass": ""
            },
            "games": []
        }

    def load(self) -> dict:
        """
        加载配置文件。

        Returns:
            配置字典
        """
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
        return self._config

    def save(self) -> None:
        """保存配置到文件。"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def config(self) -> dict:
        """获取当前配置。"""
        return self._config

    # ========== 用户配置 ==========

    def get_user(self) -> dict:
        """获取用户配置。"""
        return self._config.get("user", {})

    def set_user(self, username: str, webdav_url: str, webdav_pass: str) -> None:
        """
        设置用户配置。

        Args:
            username: 用户名
            webdav_url: WebDAV 服务地址
            webdav_pass: WebDAV 密码
        """
        self._config["user"] = {
            "username": username,
            "webdav_url": webdav_url,
            "webdav_pass": webdav_pass
        }
        self.save()

    def get_password(self) -> Optional[str]:
        """获取 WebDAV 密码。"""
        return self._config.get("user", {}).get("webdav_pass")

    def is_user_configured(self) -> bool:
        """检查用户是否已配置。"""
        user = self.get_user()
        return bool(
            user.get("username") and
            user.get("webdav_url") and
            user.get("webdav_pass")
        )

    def clear_user(self) -> None:
        """清除用户配置。"""
        self._config["user"] = {"username": "", "webdav_url": "", "webdav_pass": ""}
        self.save()

    # ========== 游戏 ID 生成 ==========

    @staticmethod
    def generate_game_id() -> str:
        """
        生成游戏 ID。

        格式: game_YYMMDD_HHMMSS

        Returns:
            游戏 ID 字符串
        """
        return "game_" + datetime.now().strftime("%y%m%d_%H%M%S")

    # ========== 名称唯一性校验 ==========

    def is_name_unique(self, name: str) -> bool:
        """
        检查游戏名称是否唯一（忽略大小写）。

        Args:
            name: 游戏名称

        Returns:
            True 如果名称唯一，False 如果已存在
        """
        name_lower = name.lower()
        for game in self._config.get("games", []):
            if game.get("name", "").lower() == name_lower:
                return False
        return True

    def find_game_by_name(self, name: str) -> Optional[dict]:
        """
        按名称查找游戏（忽略大小写）。

        Args:
            name: 游戏名称

        Returns:
            游戏配置字典，未找到返回 None
        """
        name_lower = name.lower()
        for game in self._config.get("games", []):
            if game.get("name", "").lower() == name_lower:
                return game
        return None

    # ========== 游戏 CRUD ==========

    def list_games(self) -> list[dict]:
        """
        列出所有游戏配置。

        Returns:
            游戏配置列表
        """
        return self._config.get("games", [])

    def get_game(self, game_id: str) -> Optional[dict]:
        """
        获取指定游戏配置。

        Args:
            game_id: 游戏 ID

        Returns:
            游戏配置字典，未找到返回 None
        """
        for game in self._config.get("games", []):
            if game.get("id") == game_id:
                return game
        return None

    def add_game(self, name: str, local_path: str, source: str = "manual") -> dict:
        """
        添加游戏配置。

        Args:
            name: 游戏名称
            local_path: 本地存档路径（可含环境变量）
            source: 路径来源，"library" 或 "manual"

        Returns:
            新创建的游戏配置

        Raises:
            ValueError: 游戏名称已存在
        """
        if not self.is_name_unique(name):
            raise ValueError(f"游戏名称已存在: {name}")

        game = {
            "id": self.generate_game_id(),
            "name": name,
            "local_path": local_path,
            "source": source,
            "last_sync": None
        }

        self._config.setdefault("games", []).append(game)
        self.save()

        return game

    def update_game(self, game_id: str, **kwargs) -> Optional[dict]:
        """
        更新游戏配置。

        Args:
            game_id: 游戏 ID
            **kwargs: 要更新的字段

        Returns:
            更新后的游戏配置，未找到返回 None
        """
        game = self.get_game(game_id)
        if not game:
            return None

        # 如果更新名称，需要检查唯一性
        if "name" in kwargs and kwargs["name"] != game["name"]:
            if not self.is_name_unique(kwargs["name"]):
                raise ValueError(f"游戏名称已存在: {kwargs['name']}")

        game.update(kwargs)
        self.save()
        return game

    def update_last_sync(self, game_id: str) -> None:
        """
        更新游戏的最后备份时间。

        Args:
            game_id: 游戏 ID
        """
        self.update_game(game_id, last_sync=datetime.now().isoformat())

    def update_last_restore(self, game_id: str) -> None:
        """
        更新游戏的最后恢复时间。

        Args:
            game_id: 游戏 ID
        """
        self.update_game(game_id, last_restore=datetime.now().isoformat())

    def remove_game(self, game_id: str) -> bool:
        """
        删除游戏配置。

        Args:
            game_id: 游戏 ID

        Returns:
            True 如果删除成功，False 如果游戏不存在
        """
        games = self._config.get("games", [])
        for i, game in enumerate(games):
            if game.get("id") == game_id:
                games.pop(i)
                self.save()
                return True
        return False

    # ========== 工具方法 ==========

    def get_game_count(self) -> int:
        """获取游戏数量。"""
        return len(self._config.get("games", []))

    def clear_all_games(self) -> None:
        """清空所有游戏配置（慎用）。"""
        self._config["games"] = []
        self.save()
