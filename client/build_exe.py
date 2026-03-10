#!/usr/bin/env python3
"""
ClawSave Client - 打包脚本

使用方法:
    python build_exe.py          # 打包
    python build_exe.py --clean  # 清理后打包
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 项目目录
PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"


def clean():
    """清理打包生成的文件"""
    print("清理打包文件...")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"  删除: {DIST_DIR}")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"  删除: {BUILD_DIR}")

    spec_file = PROJECT_DIR / "clawsave.spec"
    if spec_file.exists() and "--keep-spec" not in sys.argv:
        # 保留 spec 文件用于自定义配置
        pass

    print("清理完成!")


def check_pyinstaller():
    """检查 PyInstaller 是否安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("  正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✓ PyInstaller 安装完成")


def build():
    """打包应用"""
    print("\n" + "=" * 50)
    print("ClawSave Client - 打包")
    print("=" * 50 + "\n")

    # 检查 PyInstaller
    check_pyinstaller()

    # 切换到项目目录
    os.chdir(PROJECT_DIR)

    # 打包命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--noconsole",
        "--onefile",
        "--name", "ClawSave",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(PROJECT_DIR),
        "main.py"
    ]

    print(f"\n执行命令:\n  {' '.join(cmd)}\n")

    # 执行打包
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("✅ 打包成功!")
        print("=" * 50)

        # 显示输出文件
        if sys.platform == "win32":
            exe_path = DIST_DIR / "ClawSave.exe"
        else:
            exe_path = DIST_DIR / "ClawSave"

        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n输出文件: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")
    else:
        print("\n" + "=" * 50)
        print("❌ 打包失败!")
        print("=" * 50)
        sys.exit(1)


def main():
    """主函数"""
    if "--clean" in sys.argv:
        clean()
        print()

    build()


if __name__ == "__main__":
    main()
