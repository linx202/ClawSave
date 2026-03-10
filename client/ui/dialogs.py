"""
ClawSave Client - 对话框组件

包含添加游戏、设置等对话框。
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, Callable

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import ConfigManager, WebDAVClient, WebDAVError, file_handler


class AddGameDialog(ctk.CTkToplevel):
    """添加游戏对话框"""

    def __init__(self, parent, on_success: Optional[Callable] = None):
        super().__init__(parent)

        self.parent = parent
        self.on_success = on_success
        self.config_manager = ConfigManager()

        # 配置窗口
        self.title("添加游戏")
        self.geometry("450x200")
        self.resizable(False, False)
        self.transient(parent)

        # 先构建 UI
        self._setup_ui()

        # 居中显示并 grab
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

        self.after(100, self.grab_set)

    def _setup_ui(self):
        """构建界面"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        # 游戏名称
        name_label = ctk.CTkLabel(main_frame, text="游戏名称:", anchor="w")
        name_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.name_entry = ctk.CTkEntry(main_frame, placeholder_text="如：塞尔达传说")
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # 存档路径
        path_label = ctk.CTkLabel(main_frame, text="存档路径:", anchor="w")
        path_label.grid(row=2, column=0, sticky="ew", pady=(0, 5))

        path_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        path_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        path_frame.grid_columnconfigure(0, weight=1)

        self.path_entry = ctk.CTkEntry(path_frame, placeholder_text="如：%APPDATA%\\GameName 或 ~/Library/Application Support/GameName")
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            path_frame,
            text="浏览",
            width=60,
            command=self._on_browse
        )
        self.browse_btn.grid(row=0, column=1)

        # 错误提示
        self.error_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color="#c53030",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.error_label.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # 按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, sticky="e")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            width=80,
            fg_color="transparent",
            border_width=1,
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="确认",
            width=80,
            command=self._on_confirm
        )
        confirm_btn.pack(side="left")

        # 绑定快捷键
        self.bind('<Return>', lambda e: self._on_confirm())
        self.bind('<Escape>', lambda e: self.destroy())
        self.name_entry.focus()

    def _on_browse(self):
        """浏览路径"""
        path = filedialog.askdirectory(title="选择存档目录")
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def _on_confirm(self):
        """确认添加"""
        name = self.name_entry.get().strip()
        path = self.path_entry.get().strip()

        if not name:
            self.error_label.configure(text="请输入游戏名称")
            return

        if not path:
            self.error_label.configure(text="请输入存档路径")
            return

        if not self.config_manager.is_name_unique(name):
            self.error_label.configure(text=f"游戏名称已存在: {name}")
            return

        # 验证路径
        expanded = file_handler.expand_path(path)
        if not os.path.exists(expanded):
            self.error_label.configure(text=f"路径不存在: {expanded}")
            return

        try:
            game = self.config_manager.add_game(name, path)
            if self.on_success:
                self.on_success(game)
            self.destroy()
        except ValueError as e:
            self.error_label.configure(text=str(e))


class SettingsDialog(ctk.CTkToplevel):
    """设置对话框"""

    def __init__(self, parent, on_success: Optional[Callable] = None):
        super().__init__(parent)

        self.parent = parent
        self.on_success = on_success
        self.config_manager = ConfigManager()

        # 配置窗口
        self.title("WebDAV 设置")
        self.geometry("450x320")
        self.resizable(False, False)
        self.transient(parent)

        # 先构建 UI
        self._setup_ui()
        self._load_current()

        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 320) // 2
        self.geometry(f"+{x}+{y}")

        self.after(100, self.grab_set)

    def _setup_ui(self):
        """构建界面"""
        # 使用 grid 布局
        self.grid_columnconfigure(0, weight=1)

        # WebDAV URL
        url_label = ctk.CTkLabel(self, text="WebDAV 地址:", anchor="w")
        url_label.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))

        self.url_entry = ctk.CTkEntry(self, placeholder_text="http://server:port")
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # 用户名
        user_label = ctk.CTkLabel(self, text="用户名:", anchor="w")
        user_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 5))

        self.user_entry = ctk.CTkEntry(self, placeholder_text="admin")
        self.user_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))

        # 密码
        pass_label = ctk.CTkLabel(self, text="密码:", anchor="w")
        pass_label.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 5))

        self.pass_entry = ctk.CTkEntry(self, placeholder_text="••••••••", show="•")
        self.pass_entry.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 10))

        # 状态提示
        self.status_label = ctk.CTkLabel(
            self,
            text=" ",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_label.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 15))

        # 按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=7, column=0, sticky="e", padx=20, pady=(0, 20))

        test_btn = ctk.CTkButton(
            btn_frame,
            text="测试连接",
            width=80,
            fg_color="#4a5568",
            hover_color="#2d3748",
            command=self._on_test
        )
        test_btn.pack(side="left", padx=(0, 10))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            width=80,
            fg_color="transparent",
            border_width=1,
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="保存",
            width=80,
            command=self._on_save
        )
        save_btn.pack(side="left")

        self.bind('<Escape>', lambda e: self.destroy())

    def _load_current(self):
        """加载当前配置"""
        user = self.config_manager.get_user()
        self.url_entry.insert(0, user.get('webdav_url', ''))
        self.user_entry.insert(0, user.get('username', ''))
        self.pass_entry.insert(0, user.get('webdav_pass', ''))

    def _on_test(self):
        """测试连接"""
        url = self.url_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not all([url, username, password]):
            self.status_label.configure(text="请填写所有字段", text_color="#c53030")
            return

        self.status_label.configure(text="测试中...", text_color="gray")

        def test_task():
            try:
                client = WebDAVClient(url, username, password)
                success = client.test_connection()
                self.after(0, lambda: self._on_test_complete(success))
            except Exception as e:
                self.after(0, lambda: self._on_test_complete(False, str(e)))

        threading.Thread(target=test_task, daemon=True).start()

    def _on_test_complete(self, success: bool, error: str = None):
        """测试完成"""
        if success:
            self.status_label.configure(text="✓ 连接成功", text_color="#38a169")
        else:
            self.status_label.configure(text=f"✗ 连接失败: {error or '未知错误'}", text_color="#c53030")

    def _on_save(self):
        """保存配置"""
        url = self.url_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not all([url, username, password]):
            self.status_label.configure(text="请填写所有字段", text_color="#c53030")
            return

        self.config_manager.set_user(username, url, password)
        self.status_label.configure(text="✓ 保存成功", text_color="#38a169")

        if self.on_success:
            self.on_success()

        self.after(500, self.destroy)


class RestoreDialog(ctk.CTkToplevel):
    """恢复版本选择对话框"""

    def __init__(self, parent, game_id: str, game_name: str, on_restore: Optional[Callable] = None):
        super().__init__(parent)

        self.parent = parent
        self.game_id = game_id
        self.game_name = game_name
        self.on_restore = on_restore
        self.selected_archive = None
        self.config_manager = ConfigManager()

        # 配置窗口
        self.title(f"恢复存档 - {game_name}")
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)

        # 先构建 UI
        self._setup_ui()

        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 350) // 2
        self.geometry(f"+{x}+{y}")

        self.after(100, self.grab_set)

        # 加载存档列表
        self._load_archives()

    def _setup_ui(self):
        """构建界面"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 提示
        tip_label = ctk.CTkLabel(main_frame, text="选择要恢复的存档版本:", anchor="w")
        tip_label.pack(fill="x", pady=(0, 10))

        # 存档列表
        self.archive_list = ctk.CTkScrollableFrame(main_frame)
        self.archive_list.pack(fill="both", expand=True, pady=(0, 10))

        # 加载状态
        self.loading_label = ctk.CTkLabel(
            self.archive_list,
            text="加载中...",
            text_color="gray"
        )
        self.loading_label.pack(pady=20)

        # 状态提示
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        # 按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            width=80,
            fg_color="transparent",
            border_width=1,
            command=self.destroy
        )
        cancel_btn.pack(side="right")

        self.restore_btn = ctk.CTkButton(
            btn_frame,
            text="恢复",
            width=80,
            state="disabled",
            command=self._on_restore
        )
        self.restore_btn.pack(side="right", padx=(0, 10))

        self.bind('<Escape>', lambda e: self.destroy())

    def _load_archives(self):
        """加载存档列表"""
        def load_task():
            try:
                user = self.config_manager.get_user()
                client = WebDAVClient(
                    user.get('webdav_url', ''),
                    user.get('username', ''),
                    user.get('webdav_pass', '')
                )

                archive_path = f"/ClawSave/users/{user.get('username')}/{self.game_id}/archives/"
                items = client.list_dir(archive_path)

                archives = [item for item in items if not item['is_dir'] and item['name'].endswith('.zip')]
                archives.sort(key=lambda x: x['name'], reverse=True)

                self.after(0, lambda: self._display_archives(archives))
            except Exception as e:
                self.after(0, lambda: self._on_load_error(str(e)))

        threading.Thread(target=load_task, daemon=True).start()

    def _display_archives(self, archives: list):
        """显示存档列表"""
        self.loading_label.destroy()

        if not archives:
            empty_label = ctk.CTkLabel(
                self.archive_list,
                text="没有找到存档",
                text_color="gray"
            )
            empty_label.pack(pady=20)
            return

        self.archive_buttons = []

        for archive in archives:
            btn = ctk.CTkButton(
                self.archive_list,
                text=f"{archive['name']}  ({self._format_size(archive['size'])})",
                fg_color="transparent",
                text_color=("gray10", "#DCE4EE"),
                border_width=1,
                anchor="w",
                command=lambda a=archive: self._select_archive(a)
            )
            btn.pack(fill="x", pady=2)
            self.archive_buttons.append(btn)

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / 1024 / 1024:.1f} MB"

    def _on_load_error(self, error: str):
        """加载失败"""
        self.loading_label.configure(text=f"加载失败: {error}", text_color="#c53030")

    def _select_archive(self, archive: dict):
        """选择存档"""
        self.selected_archive = archive

        for btn in self.archive_buttons:
            btn.configure(fg_color="transparent")

        for btn in self.archive_buttons:
            if archive['name'] in btn.cget("text"):
                btn.configure(fg_color=("#3b82f6", "#1d4ed8"))
                break

        self.restore_btn.configure(state="normal")
        self.status_label.configure(text=f"已选择: {archive['name']}")

    def _on_restore(self):
        """确认恢复"""
        if self.selected_archive and self.on_restore:
            self.on_restore(self.game_id, self.selected_archive['name'])
        self.destroy()
