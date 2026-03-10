"""
ClawSave Client - P0 核心模块测试

运行方式: python -m client.test_core
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.core import file_handler, config_manager, meta_manager, credential_manager


def test_file_handler():
    """测试文件处理模块"""
    print("\n=== 测试 file_handler ===")

    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件结构
        test_dir = Path(tmpdir) / "test_game"
        test_dir.mkdir()
        (test_dir / "save1.dat").write_text("save data 1")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "save2.dat").write_text("save data 2")

        # 测试 expand_path
        expanded = file_handler.expand_path(str(test_dir))
        assert os.path.isabs(expanded), "expand_path 应返回绝对路径"
        print("✓ expand_path 正常")

        # 测试 pack_directory
        zip_path = file_handler.pack_directory(str(test_dir))
        assert os.path.exists(zip_path), "压缩文件应存在"
        assert zip_path.endswith(".zip"), "文件名应以 .zip 结尾"
        print(f"✓ pack_directory 正常: {Path(zip_path).name}")

        # 测试 unpack_archive
        extract_dir = Path(tmpdir) / "extracted"
        file_handler.unpack_archive(zip_path, str(extract_dir))
        assert (extract_dir / "save1.dat").exists(), "解压后应包含 save1.dat"
        assert (extract_dir / "subdir" / "save2.dat").exists(), "解压后应包含 subdir/save2.dat"
        print("✓ unpack_archive 正常")

        # 测试 get_directory_size
        size = file_handler.get_directory_size(str(test_dir))
        assert size > 0, "目录大小应大于 0"
        print(f"✓ get_directory_size 正常: {size} bytes")

        # 清理生成的 zip 文件
        if os.path.exists(zip_path):
            os.unlink(zip_path)


def test_config_manager():
    """测试配置管理模块"""
    print("\n=== 测试 config_manager ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        cm = config_manager.ConfigManager(str(config_path))

        # 测试初始配置
        assert cm.config["config_version"] == "1.0", "配置版本应为 1.0"
        assert cm.list_games() == [], "初始游戏列表应为空"
        print("✓ 初始配置正常")

        # 测试用户配置（密码存储在密钥环）
        cm.set_user("testuser_clawsave", "http://localhost:8080", "testpass")
        assert cm.is_user_configured(), "用户应已配置"
        user = cm.get_user()
        assert user["username"] == "testuser_clawsave"
        assert "webdav_pass" not in user, "配置中不应包含密码"
        assert cm.get_password() == "testpass", "应能从密钥环获取密码"
        print("✓ 用户配置正常（密码安全存储）")

        # 测试 ID 生成
        game_id = cm.generate_game_id()
        assert game_id.startswith("game_"), "ID 应以 game_ 开头"
        print(f"✓ ID 生成正常: {game_id}")

        # 测试添加游戏
        game1 = cm.add_game("塞尔达传说", "/path/to/zelda")
        assert game1["id"].startswith("game_")
        assert game1["name"] == "塞尔达传说"
        assert cm.get_game_count() == 1
        print(f"✓ 添加游戏正常: {game1['id']}")

        # 测试名称唯一性
        assert not cm.is_name_unique("塞尔达传说"), "同名应不唯一"
        assert not cm.is_name_unique("塞尔达传说".upper()), "同名（不同大小写）应不唯一"
        assert cm.is_name_unique("马里奥"), "不同名应唯一"
        print("✓ 名称唯一性校验正常")

        # 测试重名添加应抛异常
        try:
            cm.add_game("塞尔达传说", "/another/path")
            assert False, "重名应抛出异常"
        except ValueError as e:
            print(f"✓ 重名拦截正常: {e}")

        # 测试获取游戏
        fetched = cm.get_game(game1["id"])
        assert fetched["name"] == "塞尔达传说"
        by_name = cm.find_game_by_name("塞尔达传说")
        assert by_name is not None
        print("✓ 获取游戏正常")

        # 测试更新游戏
        cm.update_game(game1["id"], local_path="/new/path")
        assert cm.get_game(game1["id"])["local_path"] == "/new/path"
        print("✓ 更新游戏正常")

        # 测试更新同步时间
        cm.update_last_sync(game1["id"])
        assert cm.get_game(game1["id"])["last_sync"] is not None
        print("✓ 更新同步时间正常")

        # 测试删除游戏
        cm.remove_game(game1["id"])
        assert cm.get_game_count() == 0
        print("✓ 删除游戏正常")

        # 测试清除用户
        cm.clear_user()
        assert not cm.is_user_configured(), "清除后用户不应已配置"
        print("✓ 清除用户正常")

        # 清理密钥环测试数据
        credential_manager.delete_password("testuser_clawsave")


def test_credential_manager():
    """测试凭证管理模块"""
    print("\n=== 测试 credential_manager ===")

    # 测试密钥环可用性
    if not credential_manager.is_keyring_available():
        print("⚠ 系统密钥环不可用，跳过测试")
        return

    print("✓ 系统密钥环可用")

    test_user = "__clawsave_test_user__"
    test_pass = "test_password_123"

    # 清理可能存在的测试数据
    credential_manager.delete_password(test_user)

    # 测试保存密码
    credential_manager.save_password(test_user, test_pass)
    print("✓ 保存密码正常")

    # 测试检查密码存在
    assert credential_manager.has_password(test_user)
    print("✓ has_password 正常")

    # 测试获取密码
    retrieved = credential_manager.get_password(test_user)
    assert retrieved == test_pass
    print("✓ 获取密码正常")

    # 测试删除密码
    credential_manager.delete_password(test_user)
    assert not credential_manager.has_password(test_user)
    print("✓ 删除密码正常")


def test_meta_manager():
    """测试元数据管理模块"""
    print("\n=== 测试 meta_manager ===")

    # 测试创建元数据
    meta = meta_manager.create_meta("塞尔达传说")
    assert meta["game_name"] == "塞尔达传说"
    assert meta["latest_backup"] is None
    assert meta["notes"] == {}
    print("✓ create_meta 正常")

    # 测试添加备份
    meta = meta_manager.add_backup(meta, "2026-03-09_10-30-00.zip", "初始备份")
    assert meta["latest_backup"] == "2026-03-09_10-30-00.zip"
    assert meta_manager.get_note(meta, "2026-03-09_10-30-00.zip") == "初始备份"
    print("✓ add_backup 正常")

    # 添加更多备份
    meta = meta_manager.add_backup(meta, "2026-03-09_12-00-00.zip", "打完四神")
    meta = meta_manager.add_backup(meta, "2026-03-09_15-30-00.zip")

    # 测试列表（按时间倒序）
    backups = meta_manager.list_backups(meta)
    assert backups[0] == "2026-03-09_15-30-00.zip", "最新的应在最前"
    assert len(backups) == 3
    print(f"✓ list_backups 正常: {backups}")

    # 测试获取最新备份
    latest = meta_manager.get_latest_backup(meta)
    assert latest == "2026-03-09_15-30-00.zip"
    print(f"✓ get_latest_backup 正常: {latest}")

    # 测试设置备注
    meta = meta_manager.set_note(meta, "2026-03-09_15-30-00.zip", "通关存档")
    assert meta_manager.get_note(meta, "2026-03-09_15-30-00.zip") == "通关存档"
    print("✓ set_note 正常")

    # 测试删除备份记录
    meta = meta_manager.remove_backup(meta, "2026-03-09_15-30-00.zip")
    assert meta_manager.get_backup_count(meta) == 2
    assert meta["latest_backup"] == "2026-03-09_12-00-00.zip", "删除最新后应更新"
    print("✓ remove_backup 正常")

    # 测试 JSON 序列化
    json_str = meta_manager.to_json(meta)
    parsed = meta_manager.from_json(json_str)
    assert parsed["game_name"] == meta["game_name"]
    print("✓ JSON 序列化正常")

    # 测试验证
    assert meta_manager.validate_meta(meta)
    assert not meta_manager.validate_meta({"invalid": "structure"})
    print("✓ validate_meta 正常")


def test_webdav_client():
    """测试 WebDAV 客户端（需要运行服务）"""
    print("\n=== 测试 webdav_client ===")
    print("⚠ 此测试需要本地 WebDAV 服务运行")
    print("  请先启动服务: cd server && docker-compose up -d")
    print("  跳过测试...")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("ClawSave P0 核心模块测试")
    print("=" * 50)

    try:
        test_file_handler()
        test_credential_manager()
        test_config_manager()
        test_meta_manager()
        test_webdav_client()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
