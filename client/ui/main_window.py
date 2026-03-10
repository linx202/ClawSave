"""
ClawSave Client - 主界面

提供游戏列表展示、备份恢复操作等核心功能。
"""

import os
import threading
import customtkinter as ctk
from typing import Optional

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    ConfigManager,
    WebDAVClient,
    WebDAVError,
    expand_path,
    pack_directory,
    unpack_archive,
    generate_archive_filename,
    create_meta,
    add_backup,
    to_json,
    from_json,
)
from ui.widgets import GameCard, StatusBar, EmptyState
from ui.dialogs import AddGameDialog, SettingsDialog, RestoreDialog


class MainWindow(ctk.CTk):
    """主窗口"""

    def __init__(self):
        """初始化主窗口"""
        super().__init__()

        # 配置管理器
        self.config_manager = ConfigManager()

        # WebDAV 客户端（延迟初始化）
        self._webdav_client: Optional[WebDAVClient] = None

        # 游戏卡片引用
        self.game_cards: dict[str, GameCard] = {}

        # 取消标志
        self._cancel_flag = False

        # 配置窗口
        self.title("ClawSave")
        self.geometry("700x600")
        self.minsize(600, 400)

        # 设置主题
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # 构建界面
        self._setup_ui()

        # 加载游戏列表
        self._refresh_game_list()

    def _setup_ui(self):
        """构建界面"""
        # 配置网格
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ===== 顶部标题栏 =====
        header_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="ClawSave",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # 连接状态
        self.connection_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.connection_label.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # 检查连接状态
        self._check_connection()

        # ===== 中部游戏列表 =====
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        # 滚动区域
        self.scroll_frame = ctk.CTkScrollableFrame(list_frame)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # ===== 底部操作区 =====
        action_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        add_btn = ctk.CTkButton(
            action_frame,
            text="+ 添加游戏",
            command=self._on_add_game
        )
        add_btn.pack(side="left")

        settings_btn = ctk.CTkButton(
            action_frame,
            text="设置",
            width=80,
            fg_color="#4a5568",
            hover_color="#2d3748",
            command=self._on_settings
        )
        settings_btn.pack(side="left", padx=(10, 0))

        # ===== 底部状态栏 =====
        self.status_bar = StatusBar(self, on_cancel=self._on_cancel)
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

    def _check_connection(self):
        """检查连接状态"""
        if not self.config_manager.is_user_configured():
            self.connection_label.configure(text="⚠ 未配置", text_color="#ecc94b")
            return

        def check_task():
            try:
                client = self._get_webdav_client()
                success = client.test_connection()
                self.after(0, lambda: self._update_connection_status(success))
            except Exception:
                self.after(0, lambda: self._update_connection_status(False))

        thread = threading.Thread(target=check_task, daemon=True)
        thread.start()

    def _update_connection_status(self, connected: bool):
        """更新连接状态显示"""
        if connected:
            user = self.config_manager.get_user()
            self.connection_label.configure(
                text=f"✓ 已连接: {user.get('username', '')}",
                text_color="#38a169"
            )
        else:
            self.connection_label.configure(text="✗ 连接失败", text_color="#c53030")

    def _get_webdav_client(self) -> WebDAVClient:
        """获取 WebDAV 客户端"""
        if self._webdav_client is None:
            user = self.config_manager.get_user()
            self._webdav_client = WebDAVClient(
                url=user.get('webdav_url', ''),
                username=user.get('username', ''),
                password=user.get('webdav_pass', '')
            )
        return self._webdav_client

    def _refresh_game_list(self):
        """刷新游戏列表"""
        # 清空现有卡片
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.game_cards.clear()

        games = self.config_manager.list_games()

        if not games:
            # 显示空状态
            empty_state = EmptyState(self.scroll_frame, on_add_game=self._on_add_game)
            empty_state.pack(fill="both", expand=True)
            self.status_bar.set_text("就绪")
            return

        # 创建游戏卡片
        for i, game in enumerate(games):
            card = GameCard(
                self.scroll_frame,
                game_data=game,
                on_backup=self._on_backup,
                on_restore=self._on_restore,
                on_delete=self._on_delete
            )
            card.grid(row=i, column=0, sticky="ew", pady=(0, 10))
            self.game_cards[game['id']] = card

        self.status_bar.set_text(f"共 {len(games)} 个游戏")

    def _on_add_game(self):
        """添加游戏"""
        def on_success(game):
            self._refresh_game_list()
            self.status_bar.set_text(f"已添加: {game['name']}")

        AddGameDialog(self, on_success=on_success)

    def _on_settings(self):
        """打开设置"""
        def on_success():
            # 重置 WebDAV 客户端
            self._webdav_client = None
            # 重新加载配置
            self.config_manager.load()
            # 重新检查连接
            self._check_connection()

        SettingsDialog(self, on_success=on_success)

    def _on_backup(self, game_id: str):
        """备份游戏"""
        game = self.config_manager.get_game(game_id)
        if not game:
            return

        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(True, "backup")

        self.status_bar.set_text(f"正在备份: {game['name']}...")
        self.status_bar.show_progress(True, show_cancel=True)
        self._cancel_flag = False

        def backup_task():
            try:
                if self._cancel_flag:
                    self.after(0, lambda: self._on_backup_cancelled(game_id))
                    return

                # 1. 压缩存档
                local_path = expand_path(game['local_path'])
                zip_path = pack_directory(local_path)
                zip_filename = os.path.basename(zip_path)

                if self._cancel_flag:
                    if os.path.exists(zip_path):
                        os.unlink(zip_path)
                    self.after(0, lambda: self._on_backup_cancelled(game_id))
                    return

                # 2. 获取 WebDAV 客户端
                client = self._get_webdav_client()
                user = self.config_manager.get_user()

                # 3. 确保目录存在
                archive_dir = f"/ClawSave/users/{user['username']}/{game_id}/archives/"
                client.mkdir(archive_dir)

                # 4. 上传存档
                remote_path = f"{archive_dir}{zip_filename}"
                client.upload(zip_path, remote_path, timeout=120)

                if self._cancel_flag:
                    if os.path.exists(zip_path):
                        os.unlink(zip_path)
                    self.after(0, lambda: self._on_backup_cancelled(game_id))
                    return

                # 5. 更新元数据
                meta_path = f"/ClawSave/users/{user['username']}/{game_id}/meta.json"
                meta = client.download_json(meta_path, timeout=30)
                if not meta:
                    meta = create_meta(game['name'])
                meta = add_backup(meta, zip_filename)
                client.upload_json(meta, meta_path, timeout=30)

                # 6. 更新本地配置
                self.config_manager.update_last_sync(game_id)

                # 7. 清理临时文件
                if os.path.exists(zip_path):
                    os.unlink(zip_path)

                self.after(0, lambda: self._on_backup_complete(game_id, game['name']))

            except Exception as e:
                self.after(0, lambda: self._on_backup_error(game_id, str(e)))

        thread = threading.Thread(target=backup_task, daemon=True)
        thread.start()

    def _on_backup_complete(self, game_id: str, game_name: str):
        """备份完成"""
        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(False, "backup")
            # 更新卡片数据
            game = self.config_manager.get_game(game_id)
            if game:
                card.update_data(game)

        self.status_bar.show_progress(False)
        self.status_bar.set_text(f"✓ 备份完成: {game_name}")

    def _on_backup_error(self, game_id: str, error: str):
        """备份失败"""
        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(False, "backup")

        self.status_bar.show_progress(False)
        self.status_bar.set_text(f"✗ 备份失败: {error}")

    def _on_backup_cancelled(self, game_id: str):
        """备份已取消"""
        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(False, "backup")

        self.status_bar.show_progress(False)
        self.status_bar.set_text("已取消备份")

    def _on_restore(self, game_id: str):
        """恢复游戏（打开选择对话框）"""
        game = self.config_manager.get_game(game_id)
        if not game:
            return

        def on_restore(gid, archive_name):
            self._do_restore(gid, archive_name)

        RestoreDialog(self, game_id, game['name'], on_restore=on_restore)

    def _do_restore(self, game_id: str, archive_name: str):
        """执行恢复"""
        game = self.config_manager.get_game(game_id)
        if not game:
            return

        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(True, "restore")

        self.status_bar.set_text(f"正在恢复: {game['name']}...")
        self.status_bar.show_progress(True, show_cancel=True)
        self._cancel_flag = False

        def restore_task():
            try:
                if self._cancel_flag:
                    self.after(0, lambda: self._on_restore_cancelled(game_id))
                    return

                user = self.config_manager.get_user()
                client = self._get_webdav_client()

                # 1. 下载存档
                remote_path = f"/ClawSave/users/{user['username']}/{game_id}/archives/{archive_name}"

                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
                    local_zip = f.name

                client.download(remote_path, local_zip, timeout=60)

                if self._cancel_flag:
                    if os.path.exists(local_zip):
                        os.unlink(local_zip)
                    self.after(0, lambda: self._on_restore_cancelled(game_id))
                    return

                # 2. 解压到目标目录
                target_path = expand_path(game['local_path'])
                unpack_archive(local_zip, target_path, overwrite=True)

                # 3. 清理临时文件
                if os.path.exists(local_zip):
                    os.unlink(local_zip)

                self.after(0, lambda: self._on_restore_complete(game_id, game['name']))

            except Exception as e:
                self.after(0, lambda: self._on_restore_error(game_id, str(e)))

        thread = threading.Thread(target=restore_task, daemon=True)
        thread.start()

    def _on_restore_complete(self, game_id: str, game_name: str):
        """恢复完成"""
        # 更新最后恢复时间
        self.config_manager.update_last_restore(game_id)

        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(False, "restore")
            # 更新卡片数据
            game = self.config_manager.get_game(game_id)
            if game:
                card.update_data(game)

        self.status_bar.show_progress(False)
        self.status_bar.set_text(f"✓ 恢复完成: {game_name}")

    def _on_restore_error(self, game_id: str, error: str):
        """恢复失败"""
        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(False, "restore")

        self.status_bar.show_progress(False)
        self.status_bar.set_text(f"✗ 恢复失败: {error}")

    def _on_restore_cancelled(self, game_id: str):
        """恢复已取消"""
        card = self.game_cards.get(game_id)
        if card:
            card.set_loading(False, "restore")

        self.status_bar.show_progress(False)
        self.status_bar.set_text("已取消恢复")

    def _on_cancel(self):
        """取消当前操作"""
        self._cancel_flag = True

    def _on_delete(self, game_id: str):
        """删除游戏"""
        game = self.config_manager.get_game(game_id)
        if not game:
            return

        # 确认对话框
        from tkinter import messagebox
        result = messagebox.askyesno(
            "确认删除",
            f"确定要删除游戏 \"{game['name']}\" 吗？\n\n"
            "注意：这只会删除本地配置，云端存档将保留。"
        )

        if result:
            self.config_manager.remove_game(game_id)
            self._refresh_game_list()
            self.status_bar.set_text(f"已删除: {game['name']}")

    def run(self):
        """启动应用"""
        self.mainloop()
