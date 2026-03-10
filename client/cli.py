#!/usr/bin/env python3
"""
ClawSave Client - 命令行界面

当 GUI 不可用时使用。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core import (
    ConfigManager,
    WebDAVClient,
    WebDAVError,
    file_handler,
    meta_manager,
)


def print_banner():
    print("=" * 50)
    print("  ClawSave - 存档同步工具 (CLI)")
    print("=" * 50)
    print()


def print_games(cm: ConfigManager):
    """打印游戏列表"""
    games = cm.list_games()
    if not games:
        print("  (暂无游戏)")
        return

    for i, game in enumerate(games, 1):
        last_sync = game.get('last_sync', '从未')
        if last_sync:
            last_sync = last_sync.replace('T', ' ')[:16]
        print(f"  {i}. {game['name']}")
        print(f"     路径: {game['local_path']}")
        print(f"     同步: {last_sync}")
        print()


def cmd_list(cm: ConfigManager):
    """列出游戏"""
    print("\n📋 游戏列表:")
    print("-" * 40)
    print_games(cm)


def cmd_add(cm: ConfigManager):
    """添加游戏"""
    print("\n➕ 添加游戏:")
    print("-" * 40)

    name = input("  游戏名称: ").strip()
    if not name:
        print("  ✗ 名称不能为空")
        return

    if not cm.is_name_unique(name):
        print(f"  ✗ 游戏名称已存在: {name}")
        return

    path = input("  存档路径: ").strip()
    if not path:
        print("  ✗ 路径不能为空")
        return

    # 验证路径
    expanded = file_handler.expand_path(path)
    if not Path(expanded).exists():
        print(f"  ✗ 路径不存在: {expanded}")
        return

    try:
        game = cm.add_game(name, path)
        print(f"  ✓ 已添加: {game['id']}")
    except ValueError as e:
        print(f"  ✗ {e}")


def cmd_backup(cm: ConfigManager, client: WebDAVClient):
    """备份存档"""
    games = cm.list_games()
    if not games:
        print("  ✗ 没有游戏")
        return

    print("\n💾 备份存档:")
    print("-" * 40)
    print_games(cm)

    try:
        idx = int(input("  选择游戏编号: ")) - 1
        if idx < 0 or idx >= len(games):
            print("  ✗ 无效编号")
            return
    except ValueError:
        print("  ✗ 请输入数字")
        return

    game = games[idx]
    print(f"\n  正在备份: {game['name']}...")

    try:
        # 1. 压缩
        local_path = file_handler.expand_path(game['local_path'])
        zip_path = file_handler.pack_directory(local_path)
        zip_filename = Path(zip_path).name
        print(f"  ✓ 压缩完成: {zip_filename}")

        # 2. 上传
        user = cm.get_user()
        archive_dir = f"/ClawSave/users/{user['username']}/{game['id']}/archives/"
        client.mkdir(archive_dir)
        remote_path = f"{archive_dir}{zip_filename}"
        client.upload(zip_path, remote_path)
        print(f"  ✓ 上传完成")

        # 3. 更新元数据
        meta_path = f"/ClawSave/users/{user['username']}/{game['id']}/meta.json"
        meta = client.download_json(meta_path)
        if not meta:
            meta = meta_manager.create_meta(game['name'])
        meta = meta_manager.add_backup(meta, zip_filename)
        client.upload_json(meta, meta_path)

        # 4. 更新本地配置
        cm.update_last_sync(game['id'])

        # 5. 清理
        Path(zip_path).unlink(missing_ok=True)

        print(f"  ✓ 备份成功!")

    except Exception as e:
        print(f"  ✗ 备份失败: {e}")


def cmd_restore(cm: ConfigManager, client: WebDAVClient):
    """恢复存档"""
    games = cm.list_games()
    if not games:
        print("  ✗ 没有游戏")
        return

    print("\n📂 恢复存档:")
    print("-" * 40)
    print_games(cm)

    try:
        idx = int(input("  选择游戏编号: ")) - 1
        if idx < 0 or idx >= len(games):
            print("  ✗ 无效编号")
            return
    except ValueError:
        print("  ✗ 请输入数字")
        return

    game = games[idx]
    user = cm.get_user()

    # 获取存档列表
    archive_dir = f"/ClawSave/users/{user['username']}/{game['id']}/archives/"
    try:
        items = client.list_dir(archive_dir)
        archives = [item for item in items if not item['is_dir'] and item['name'].endswith('.zip')]
        archives.sort(key=lambda x: x['name'], reverse=True)
    except Exception as e:
        print(f"  ✗ 获取存档列表失败: {e}")
        return

    if not archives:
        print("  ✗ 没有存档")
        return

    print(f"\n  存档列表 ({game['name']}):")
    for i, arc in enumerate(archives, 1):
        print(f"    {i}. {arc['name']}")

    try:
        arc_idx = int(input("\n  选择存档编号: ")) - 1
        if arc_idx < 0 or arc_idx >= len(archives):
            print("  ✗ 无效编号")
            return
    except ValueError:
        print("  ✗ 请输入数字")
        return

    archive = archives[arc_idx]
    print(f"\n  正在恢复: {archive['name']}...")

    try:
        import tempfile

        # 1. 下载
        remote_path = f"{archive_dir}{archive['name']}"
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            local_zip = f.name

        client.download(remote_path, local_zip)
        print(f"  ✓ 下载完成")

        # 2. 解压
        target_path = file_handler.expand_path(game['local_path'])
        file_handler.unpack_archive(local_zip, target_path)
        print(f"  ✓ 解压完成")

        # 3. 清理
        Path(local_zip).unlink(missing_ok=True)

        print(f"  ✓ 恢复成功!")

    except Exception as e:
        print(f"  ✗ 恢复失败: {e}")


def cmd_settings(cm: ConfigManager):
    """设置"""
    print("\n⚙️ 设置:")
    print("-" * 40)

    user = cm.get_user()
    print(f"  当前 WebDAV URL: {user.get('webdav_url', '(未设置)')}")
    print(f"  当前用户名: {user.get('username', '(未设置)')}")
    print()

    url = input("  WebDAV URL: ").strip()
    if not url:
        url = user.get('webdav_url', '')

    username = input("  用户名: ").strip()
    if not username:
        username = user.get('username', '')

    password = input("  密码: ").strip()

    if not all([url, username, password]):
        print("  ✗ 请填写所有字段")
        return

    # 测试连接
    print("  测试连接...")
    try:
        test_client = WebDAVClient(url, username, password)
        if test_client.test_connection():
            cm.set_user(username, url, password)
            print("  ✓ 设置已保存")
        else:
            print("  ✗ 连接失败")
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")


def main():
    print_banner()

    cm = ConfigManager()
    client = None

    def get_client():
        nonlocal client
        if client is None:
            if not cm.is_user_configured():
                print("⚠️ 请先配置 WebDAV 连接 (命令: s)")
                return None
            user = cm.get_user()
            client = WebDAVClient(
                url=user['webdav_url'],
                username=user['username'],
                password=cm.get_password()
            )
        return client

    while True:
        print()
        print("命令: [l]列表 [a]添加 [b]备份 [r]恢复 [s]设置 [q]退出")
        cmd = input("> ").strip().lower()

        if cmd in ('l', 'list'):
            cmd_list(cm)
        elif cmd in ('a', 'add'):
            cmd_add(cm)
        elif cmd in ('b', 'backup'):
            c = get_client()
            if c:
                cmd_backup(cm, c)
        elif cmd in ('r', 'restore'):
            c = get_client()
            if c:
                cmd_restore(cm, c)
        elif cmd in ('s', 'settings'):
            cmd_settings(cm)
        elif cmd in ('q', 'quit', 'exit'):
            print("\n再见!")
            break
        else:
            print("  未知命令")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n再见!")
