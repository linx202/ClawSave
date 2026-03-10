"""
ClawSave Client - 元数据管理

负责云端 meta.json 的读写操作，管理存档备份记录和备注。
"""

import json
from datetime import datetime
from typing import Optional


def create_meta(game_name: str) -> dict:
    """
    创建初始元数据结构。

    Args:
        game_name: 游戏名称

    Returns:
        初始化的元数据字典
    """
    return {
        "game_name": game_name,
        "latest_backup": None,
        "notes": {}
    }


def add_backup(meta: dict, filename: str, note: Optional[str] = None) -> dict:
    """
    添加备份记录到元数据。

    Args:
        meta: 元数据字典
        filename: 备份文件名 (YYYY-MM-DD_HH-MM-SS.zip)
        note: 可选的备注

    Returns:
        更新后的元数据
    """
    meta["latest_backup"] = filename
    # 总是记录备份，即使没有备注
    meta.setdefault("notes", {})[filename] = note or ""
    return meta


def update_latest(meta: dict, filename: str) -> dict:
    """
    更新最新备份记录。

    Args:
        meta: 元数据字典
        filename: 备份文件名

    Returns:
        更新后的元数据
    """
    meta["latest_backup"] = filename
    return meta


def get_note(meta: dict, filename: str) -> Optional[str]:
    """
    获取指定备份的备注。

    Args:
        meta: 元数据字典
        filename: 备份文件名

    Returns:
        备注内容，未找到返回 None
    """
    return meta.get("notes", {}).get(filename)


def set_note(meta: dict, filename: str, note: str) -> dict:
    """
    设置备份的备注。

    Args:
        meta: 元数据字典
        filename: 备份文件名
        note: 备注内容

    Returns:
        更新后的元数据
    """
    meta.setdefault("notes", {})[filename] = note
    return meta


def remove_note(meta: dict, filename: str) -> dict:
    """
    删除备份的备注。

    Args:
        meta: 元数据字典
        filename: 备份文件名

    Returns:
        更新后的元数据
    """
    meta.get("notes", {}).pop(filename, None)
    return meta


def list_backups(meta: dict) -> list[str]:
    """
    列出所有备份文件名（按时间倒序）。

    由于文件名格式为 YYYY-MM-DD_HH-MM-SS.zip，
    字符串自然排序即可保证时间顺序。

    Args:
        meta: 元数据字典

    Returns:
        备份文件名列表（最新的在前）
    """
    notes = meta.get("notes", {})
    # 按文件名降序排列（最新在前）
    return sorted(notes.keys(), reverse=True)


def get_latest_backup(meta: dict) -> Optional[str]:
    """
    获取最新备份文件名。

    Args:
        meta: 元数据字典

    Returns:
        最新备份文件名，无备份返回 None
    """
    return meta.get("latest_backup")


def get_backup_count(meta: dict) -> int:
    """
    获取备份数量。

    Args:
        meta: 元数据字典

    Returns:
        备份数量
    """
    return len(meta.get("notes", {}))


def remove_backup(meta: dict, filename: str) -> dict:
    """
    从元数据中移除备份记录。

    如果移除的是最新备份，会自动更新 latest_backup 为次新的备份。

    Args:
        meta: 元数据字典
        filename: 备份文件名

    Returns:
        更新后的元数据
    """
    notes = meta.get("notes", {})
    notes.pop(filename, None)

    # 如果移除的是最新备份，更新 latest_backup
    if meta.get("latest_backup") == filename:
        backups = sorted(notes.keys(), reverse=True)
        meta["latest_backup"] = backups[0] if backups else None

    return meta


def to_json(meta: dict) -> str:
    """
    将元数据序列化为 JSON 字符串。

    Args:
        meta: 元数据字典

    Returns:
        JSON 字符串
    """
    return json.dumps(meta, indent=2, ensure_ascii=False)


def from_json(json_str: str) -> dict:
    """
    从 JSON 字符串解析元数据。

    Args:
        json_str: JSON 字符串

    Returns:
        元数据字典
    """
    return json.loads(json_str)


def validate_meta(meta: dict) -> bool:
    """
    验证元数据结构是否有效。

    Args:
        meta: 元数据字典

    Returns:
        True 如果结构有效
    """
    required_keys = ["game_name", "latest_backup", "notes"]
    return all(key in meta for key in required_keys)
