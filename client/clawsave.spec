# -*- mode: python ; coding: utf-8 -*-
"""
ClawSave Client - PyInstaller 打包配置

使用方法:
    pyinstaller clawsave.spec
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(SPECPATH).parent

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'customtkinter',
        'requests',
        'core',
        'core.config_manager',
        'core.webdav_client',
        'core.file_handler',
        'core.meta_manager',
        'core.retry_handler',
        'core.library_manager',
        'core.credential_manager',
        'ui',
        'ui.main_window',
        'ui.dialogs',
        'ui.widgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'pydoc',
        'doctest',
        'difflib',
        'inspect',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClawSave',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标: icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClawSave',
)
