"""
ClawSave Client - WebDAV 集成测试

测试完整的备份/恢复流程。
需要先配置正确的 WebDAV 凭证。
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from client.core import (
    ConfigManager,
    WebDAVClient,
    WebDAVError,
    file_handler,
    meta_manager,
)


def test_webdav_integration():
    """WebDAV 集成测试"""
    print("=" * 50)
    print("WebDAV 集成测试")
    print("=" * 50)

    # 加载配置
    cm = ConfigManager()
    if not cm.is_user_configured():
        print("❌ 请先配置 WebDAV 凭证: python3 -m client.setup_credentials")
        return False

    user = cm.get_user()
    client = WebDAVClient(
        url=user['webdav_url'],
        username=user['username'],
        password=cm.get_password()
    )

    # 测试连接
    print("\n1. 测试连接...")
    if not client.test_connection():
        print("❌ 连接失败")
        return False
    print("✅ 连接成功")

    # 测试目录创建
    test_dir = f"/ClawSave/users/{user['username']}/test_game_{datetime.now().strftime('%H%M%S')}"
    print(f"\n2. 创建测试目录: {test_dir}")
    try:
        client.mkdir(test_dir)
        client.mkdir(f"{test_dir}/archives")
        print("✅ 目录创建成功")
    except WebDAVError as e:
        print(f"❌ 创建目录失败: {e}")
        return False

    # 创建本地测试文件
    with tempfile.TemporaryDirectory() as tmpdir:
        test_save_dir = Path(tmpdir) / "save_data"
        test_save_dir.mkdir()
        (test_save_dir / "save1.dat").write_text("test save data 1")
        (test_save_dir / "config.ini").write_text("[game]\nname=test")

        # 测试压缩
        print("\n3. 压缩存档...")
        zip_path = file_handler.pack_directory(str(test_save_dir))
        print(f"✅ 压缩完成: {Path(zip_path).name}")

        # 测试上传
        remote_file = f"{test_dir}/archives/{Path(zip_path).name}"
        print(f"\n4. 上传存档: {remote_file}")
        try:
            client.upload(zip_path, remote_file)
            print("✅ 上传成功")
        except WebDAVError as e:
            print(f"❌ 上传失败: {e}")
            return False

        # 测试列表
        print(f"\n5. 列出存档:")
        try:
            items = client.list_dir(f"{test_dir}/archives")
            for item in items:
                icon = "📁" if item['is_dir'] else "📄"
                print(f"  {icon} {item['name']} ({item['size']} bytes)")
        except WebDAVError as e:
            print(f"❌ 列表失败: {e}")
            return False

        # 测试下载
        download_dir = Path(tmpdir) / "downloaded"
        download_dir.mkdir()
        download_file = download_dir / Path(zip_path).name
        print(f"\n6. 下载存档...")
        try:
            client.download(remote_file, str(download_file))
            print(f"✅ 下载完成: {download_file.stat().st_size} bytes")
        except WebDAVError as e:
            print(f"❌ 下载失败: {e}")
            return False

        # 测试解压
        print("\n7. 解压存档...")
        extract_dir = download_dir / "extracted"
        file_handler.unpack_archive(str(download_file), str(extract_dir))
        print(f"✅ 解压完成")
        print(f"  - save1.dat: {(extract_dir / 'save1.dat').read_text()}")
        print(f"  - config.ini: {(extract_dir / 'config.ini').read_text()}")

        # 测试上传 JSON
        print("\n8. 上传元数据...")
        meta = meta_manager.create_meta("测试游戏")
        meta = meta_manager.add_backup(meta, Path(zip_path).name, "集成测试")
        try:
            client.upload_json(meta, f"{test_dir}/meta.json")
            print("✅ 元数据上传成功")
        except WebDAVError as e:
            print(f"❌ 元数据上传失败: {e}")
            return False

        # 测试下载 JSON
        print("\n9. 下载元数据...")
        downloaded_meta = client.download_json(f"{test_dir}/meta.json")
        if downloaded_meta:
            print(f"✅ 元数据下载成功")
            print(f"  - 游戏名: {downloaded_meta.get('game_name')}")
            print(f"  - 最新备份: {downloaded_meta.get('latest_backup')}")
        else:
            print("❌ 元数据下载失败")
            return False

        # 清理测试文件
        os.unlink(zip_path)

    # 清理测试目录
    print(f"\n10. 清理测试数据...")
    try:
        client.delete(test_dir)
        print("✅ 清理完成")
    except WebDAVError as e:
        print(f"⚠ 清理失败: {e}")

    print("\n" + "=" * 50)
    print("✅ 所有集成测试通过!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    try:
        success = test_webdav_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
