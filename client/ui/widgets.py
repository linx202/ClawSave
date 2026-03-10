"""
ClawSave Client - 自定义组件

包含游戏卡片、状态栏等可复用组件。
"""

import customtkinter as ctk
from typing import Callable, Optional


class GameCard(ctk.CTkFrame):
    """
    游戏卡片组件

    显示单个游戏的信息和操作按钮。
    """

    def __init__(
        self,
        parent,
        game_data: dict,
        on_backup: Callable[[str], None],
        on_restore: Callable[[str], None],
        on_delete: Optional[Callable[[str], None]] = None
    ):
        """
        初始化游戏卡片。

        Args:
            parent: 父组件
            game_data: 游戏数据字典
            on_backup: 备份回调
            on_restore: 恢复回调
            on_delete: 删除回调（可选）
        """
        super().__init__(parent)

        self.game_data = game_data
        self.game_id = game_data.get('id', '')
        self.on_backup = on_backup
        self.on_restore = on_restore
        self.on_delete = on_delete

        self._setup_ui()

    def _setup_ui(self):
        """构建卡片布局"""
        # 配置网格权重
        self.grid_columnconfigure(1, weight=1)

        # 左侧图标
        self.icon_label = ctk.CTkLabel(
            self,
            text="🎮",
            font=ctk.CTkFont(size=28),
            width=40
        )
        self.icon_label.grid(row=0, column=0, rowspan=3, padx=(10, 5), pady=10, sticky="nse")

        # 第一行：游戏名称
        self.name_label = ctk.CTkLabel(
            self,
            text=self.game_data.get('name', '未知游戏'),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.name_label.grid(row=0, column=1, padx=(5, 10), pady=(10, 0), sticky="ew")

        # 第二行：路径
        path = self.game_data.get('local_path', '')
        if len(path) > 50:
            path = path[:47] + "..."
        self.path_label = ctk.CTkLabel(
            self,
            text=f"路径: {path}" if path else "路径: 未设置",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        self.path_label.grid(row=1, column=1, padx=(5, 10), pady=0, sticky="ew")

        # 第三行：同步/恢复时间
        time_text = self._format_time_info()
        self.time_label = ctk.CTkLabel(
            self,
            text=time_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        self.time_label.grid(row=2, column=1, padx=(5, 10), pady=(0, 10), sticky="ew")

        # 按钮区域
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, rowspan=3, padx=10, pady=10, sticky="e")

        # 备份按钮
        self.backup_btn = ctk.CTkButton(
            self.btn_frame,
            text="备份",
            width=60,
            command=self._on_backup_click
        )
        self.backup_btn.pack(side="left", padx=(0, 5))

        # 恢复按钮
        self.restore_btn = ctk.CTkButton(
            self.btn_frame,
            text="恢复",
            width=60,
            fg_color="#4a5568",
            hover_color="#2d3748",
            command=self._on_restore_click
        )
        self.restore_btn.pack(side="left", padx=(0, 5))

        # 删除按钮（可选）
        if self.on_delete:
            self.delete_btn = ctk.CTkButton(
                self.btn_frame,
                text="删除",
                width=60,
                fg_color="#c53030",
                hover_color="#9b2c2c",
                command=self._on_delete_click
            )
            self.delete_btn.pack(side="left")

    def _format_time_info(self) -> str:
        """格式化时间信息"""
        parts = []

        # 最后备份时间
        last_sync = self.game_data.get('last_sync')
        if last_sync:
            last_sync = last_sync.replace('T', ' ')[:19]
            parts.append(f"最后备份: {last_sync}")
        else:
            parts.append("最后备份: 未备份")

        # 最后恢复时间（如果有）
        last_restore = self.game_data.get('last_restore')
        if last_restore:
            last_restore = last_restore.replace('T', ' ')[:19]
            parts.append(f"最后恢复: {last_restore}")

        return "  |  ".join(parts)

    def _on_backup_click(self):
        """备份按钮点击"""
        if self.on_backup:
            self.on_backup(self.game_id)

    def _on_restore_click(self):
        """恢复按钮点击"""
        if self.on_restore:
            self.on_restore(self.game_id)

    def _on_delete_click(self):
        """删除按钮点击"""
        if self.on_delete:
            self.on_delete(self.game_id)

    def update_data(self, game_data: dict):
        """更新卡片数据"""
        self.game_data = game_data
        self.name_label.configure(text=game_data.get('name', '未知游戏'))

        # 更新路径
        path = game_data.get('local_path', '')
        if len(path) > 50:
            path = path[:47] + "..."
        self.path_label.configure(text=f"路径: {path}" if path else "路径: 未设置")

        # 更新时间信息
        self.time_label.configure(text=self._format_time_info())

    def set_loading(self, loading: bool, button_type: str = "backup"):
        """设置加载状态"""
        if button_type == "backup":
            btn = self.backup_btn
            text = "备份"
        else:
            btn = self.restore_btn
            text = "恢复"

        if loading:
            btn.configure(text="...", state="disabled")
        else:
            btn.configure(text=text, state="normal")


class StatusBar(ctk.CTkFrame):
    """
    状态栏组件

    显示当前状态、完成时间和进度。
    """

    def __init__(self, parent, on_cancel: Optional[Callable[[], None]] = None):
        """初始化状态栏"""
        super().__init__(parent, height=30)
        self.grid_columnconfigure(0, weight=1)
        self.on_cancel = on_cancel

        self._setup_ui()

    def _setup_ui(self):
        """构建状态栏布局"""
        # 状态文本
        self.status_label = ctk.CTkLabel(
            self,
            text="就绪",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # 完成时间显示
        self.time_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="e"
        )
        self.time_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        # 进度条（默认隐藏）
        self.progress_bar = ctk.CTkProgressBar(self, width=100)
        self.progress_bar.set(0)

        # 取消按钮（默认隐藏）
        self.cancel_btn = ctk.CTkButton(
            self,
            text="✕",
            width=30,
            height=24,
            fg_color="transparent",
            hover_color="#e53e3e",
            text_color=("gray10", "#DCE4EE"),
            command=self._on_cancel_click
        )

    def set_text(self, text: str, show_time: bool = True):
        """设置状态文本（默认显示时间）"""
        self.status_label.configure(text=text)
        if show_time:
            from datetime import datetime
            now = datetime.now().strftime("%H:%M:%S")
            self.time_label.configure(text=now)

    def show_progress(self, show: bool = True, show_cancel: bool = False):
        """显示/隐藏进度条"""
        if show:
            self.progress_bar.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            if show_cancel:
                self.cancel_btn.grid(row=0, column=3, padx=(0, 10), pady=5, sticky="e")
            else:
                self.cancel_btn.grid_forget()
            # 进度中清除时间
            self.time_label.configure(text="")
        else:
            self.progress_bar.grid_forget()
            self.cancel_btn.grid_forget()

    def set_progress(self, value: float):
        """设置进度值 (0.0 - 1.0)"""
        self.progress_bar.set(value)

    def _on_cancel_click(self):
        """取消按钮点击"""
        if self.on_cancel:
            self.on_cancel()


class EmptyState(ctk.CTkFrame):
    """
    空状态组件

    当没有游戏时显示的占位内容。
    """

    def __init__(self, parent, on_add_game: Callable[[], None]):
        """初始化空状态组件"""
        super().__init__(parent, fg_color="transparent")

        self.on_add_game = on_add_game
        self._setup_ui()

    def _setup_ui(self):
        """构建空状态布局"""
        # 居中容器
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 内容框架
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=0)

        # 图标
        icon = ctk.CTkLabel(
            content,
            text="📁",
            font=ctk.CTkFont(size=48)
        )
        icon.pack(pady=(0, 10))

        # 提示文本
        text = ctk.CTkLabel(
            content,
            text="还没有添加游戏",
            font=ctk.CTkFont(size=16)
        )
        text.pack(pady=(0, 5))

        # 副标题
        subtitle = ctk.CTkLabel(
            content,
            text="点击下方按钮添加你的第一个游戏",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 20))

        # 添加按钮
        add_btn = ctk.CTkButton(
            content,
            text="+ 添加游戏",
            command=self.on_add_game
        )
        add_btn.pack()
