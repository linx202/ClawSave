"""
ClawSave Client - 文件处理层

负责本地文件的路径解析、压缩和解压操作。
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional


def expand_path(path: str) -> str:
    """
    解析包含环境变量的路径。

    支持 Windows 风格 (%APPDATA%) 和 Unix 风格 ($HOME) 的环境变量。

    Args:
        path: 可能包含环境变量的路径

    Returns:
        解析后的绝对路径
    """
    # 先展开环境变量
    expanded = os.path.expandvars(path)
    # 再展开用户目录 (~)
    expanded = os.path.expanduser(expanded)
    # 转为绝对路径
    return os.path.abspath(expanded)


def generate_archive_filename() -> str:
    """
    生成存档文件名。

    格式: YYYY-MM-DD_HH-MM-SS.zip

    Returns:
        格式化的存档文件名
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".zip"


def pack_directory(src_dir: str, dest_zip: Optional[str] = None) -> str:
    """
    将目录打包为 zip 文件。

    Args:
        src_dir: 源目录路径
        dest_zip: 目标 zip 文件路径，如不指定则在源目录父目录生成

    Returns:
        生成的 zip 文件路径

    Raises:
        FileNotFoundError: 源目录不存在
        ValueError: 源路径不是目录
    """
    src_path = Path(expand_path(src_dir))

    if not src_path.exists():
        raise FileNotFoundError(f"源目录不存在: {src_path}")
    if not src_path.is_dir():
        raise ValueError(f"源路径不是目录: {src_path}")

    # 确定目标文件路径
    if dest_zip is None:
        dest_zip = str(src_path.parent / generate_archive_filename())
    else:
        dest_zip = expand_path(dest_zip)

    # 确保目标目录存在
    Path(dest_zip).parent.mkdir(parents=True, exist_ok=True)

    # 创建 zip 文件
    with zipfile.ZipFile(dest_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src_path):
            for file in files:
                file_path = Path(root) / file
                # 计算相对路径，保持目录结构
                arcname = file_path.relative_to(src_path)
                zf.write(file_path, arcname)

    return dest_zip


def unpack_archive(zip_path: str, dest_dir: str, overwrite: bool = True) -> None:
    """
    解压 zip 文件到指定目录。

    Args:
        zip_path: zip 文件路径
        dest_dir: 目标目录路径
        overwrite: 是否覆盖已存在的文件，默认 True

    Raises:
        FileNotFoundError: zip 文件不存在
        zipfile.BadZipFile: zip 文件损坏
    """
    zip_path = expand_path(zip_path)
    dest_path = Path(expand_path(dest_dir))

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"zip 文件不存在: {zip_path}")

    # 确保目标目录存在
    dest_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            # 解析成员路径
            member_path = dest_path / member

            # 安全检查：防止路径遍历攻击
            try:
                member_path.resolve().relative_to(dest_path.resolve())
            except ValueError:
                raise ValueError(f"不安全的路径: {member}")

            if member.endswith('/'):
                # 目录
                member_path.mkdir(parents=True, exist_ok=True)
            else:
                # 文件
                if not overwrite and member_path.exists():
                    continue
                member_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(member_path, 'wb') as dst:
                    dst.write(src.read())


def get_directory_size(path: str) -> int:
    """
    计算目录大小（字节）。

    Args:
        path: 目录路径

    Returns:
        目录总大小（字节）
    """
    path = expand_path(path)
    total = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            total += os.path.getsize(os.path.join(root, file))
    return total
