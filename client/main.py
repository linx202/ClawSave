"""
ClawSave Client - 应用入口
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow


def main():
    """主函数入口"""
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        import traceback
        print(f"启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
