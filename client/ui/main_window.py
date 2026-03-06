"""
ClawSave Client - 主界面
"""

import customtkinter as ctk


class MainWindow(ctk.CTk):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.title("ClawSave")
        self.geometry("800x600")
        self._setup_ui()

    def _setup_ui(self):
        """构建界面"""
        # TODO: 实现主界面布局
        pass

    def run(self):
        """启动应用"""
        self.mainloop()
