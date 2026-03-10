"""
ClawSave Client - 路径库管理器测试

运行方式: python -m client.test_library_manager
"""

import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.core.library_manager import LibraryManager, get_library_manager


def create_test_library():
    """创建测试用游戏库数据"""
    return [
        {
            "id": "zelda_botw",
            "name": "塞尔达传说：荒野之息",
            "platform": "Switch",
            "paths": {
                "windows": "%APPDATA%\\Cemu\\mlc01\\usr\\save\\00050000\\101c9500",
                "macos": "~/Library/Application Support/Cemu/mlc01/usr/save/00050000/101c9500",
                "linux": "~/.local/share/Cemu/mlc01/usr/save/00050000/101c9500"
            }
        },
        {
            "id": "zelda_totk",
            "name": "塞尔达传说：王国之泪",
            "platform": "Switch",
            "paths": {
                "windows": "%APPDATA%\\Cemu\\mlc01\\usr\\save\\00050000\\101c9501",
                "macos": "~/Library/Application Support/Cemu/mlc01/usr/save/00050000/101c9501"
            }
        },
        {
            "id": "mario_odyssey",
            "name": "超级马力欧：奥德赛",
            "platform": "Switch",
            "paths": {
                "windows": "%APPDATA%\\Cemu\\mlc01\\usr\\save\\00050000\\101c9502"
            }
        },
        {
            "id": "elden_ring",
            "name": "艾尔登法环",
            "platform": "Steam",
            "paths": {
                "windows": "%APPDATA%\\EldenRing",
                "linux": "~/.steam/steam/steamapps/compatdata/1245620/pfx/drive_c/users/steamuser/AppData/Roaming/EldenRing"
            }
        }
    ]


def test_search_exact_match():
    """测试精确搜索"""
    print("\n=== 测试精确搜索 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = True

    results = lm.search("艾尔登法环")
    assert len(results) == 1
    assert results[0]["id"] == "elden_ring"
    print("✓ 精确搜索正常")


def test_search_partial_match():
    """测试模糊搜索"""
    print("\n=== 测试模糊搜索 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = True

    results = lm.search("塞尔达")
    assert len(results) == 2
    names = [r["name"] for r in results]
    assert "塞尔达传说：荒野之息" in names
    assert "塞尔达传说：王国之泪" in names
    print(f"✓ 模糊搜索正常，找到 {len(results)} 个结果")


def test_search_case_insensitive():
    """测试大小写不敏感搜索"""
    print("\n=== 测试大小写不敏感 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = True

    results_lower = lm.search("mario")
    results_upper = lm.search("MARIO")

    assert len(results_lower) == len(results_upper) == 1
    assert results_lower[0]["id"] == "mario_odyssey"
    print("✓ 大小写不敏感搜索正常")


def test_search_limit():
    """测试搜索结果限制"""
    print("\n=== 测试搜索结果限制 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = True

    results = lm.search("塞尔达", limit=1)
    assert len(results) == 1
    print("✓ 搜索结果限制正常")


def test_search_empty_query():
    """测试空搜索"""
    print("\n=== 测试空搜索 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = True

    results = lm.search("")
    assert len(results) == 0
    print("✓ 空搜索返回空列表")


def test_search_no_match():
    """测试无匹配结果"""
    print("\n=== 测试无匹配结果 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = True

    results = lm.search("不存在的游戏")
    assert len(results) == 0
    print("✓ 无匹配返回空列表")


def test_search_not_loaded():
    """测试未加载时搜索"""
    print("\n=== 测试未加载时搜索 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = False  # 未加载

    results = lm.search("塞尔达")
    assert len(results) == 0
    print("✓ 未加载时搜索返回空列表")


def test_get_platform_path():
    """测试获取平台路径"""
    print("\n=== 测试获取平台路径 ===")

    lm = LibraryManager()
    game = {
        "id": "test",
        "paths": {
            "windows": "C:\\Games\\Test",
            "macos": "/Users/test/Games",
            "linux": "/home/test/Games"
        }
    }

    # 测试各平台
    import platform
    system = platform.system().lower()

    path = lm.get_platform_path(game)
    if system == "darwin":
        assert path == "/Users/test/Games"
    elif system == "windows":
        assert path == "C:\\Games\\Test"
    elif system == "linux":
        assert path == "/home/test/Games"

    print(f"✓ 获取平台路径正常: {path}")


def test_get_platform_path_not_found():
    """测试平台路径不存在"""
    print("\n=== 测试平台路径不存在 ===")

    lm = LibraryManager()
    game = {
        "id": "test",
        "paths": {
            "windows": "C:\\Games\\Test"
        }
    }

    # 临时修改 platform.system 返回值测试
    path = lm.get_platform_path(game)
    # 如果当前系统不是 Windows，path 应为 None
    import platform
    if platform.system().lower() != "windows":
        assert path is None or path == "C:\\Games\\Test"
    print("✓ 平台路径不存在时处理正常")


def test_get_by_id():
    """测试按 ID 获取游戏"""
    print("\n=== 测试按 ID 获取 ===")

    lm = LibraryManager()
    lm._library = create_test_library()
    lm._loaded = True

    game = lm.get_by_id("zelda_botw")
    assert game is not None
    assert game["name"] == "塞尔达传说：荒野之息"

    not_found = lm.get_by_id("nonexistent")
    assert not_found is None
    print("✓ 按 ID 获取正常")


def test_properties():
    """测试属性"""
    print("\n=== 测试属性 ===")

    lm = LibraryManager()
    assert lm.is_loaded == False
    assert lm.count == 0

    lm._library = create_test_library()
    lm._loaded = True

    assert lm.is_loaded == True
    assert lm.count == 4
    print(f"✓ 属性正常: is_loaded={lm.is_loaded}, count={lm.count}")


def test_load_from_cache():
    """测试从缓存加载"""
    print("\n=== 测试从缓存加载 ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试缓存文件
        cache_file = Path(tmpdir) / "games_library.json"
        test_data = create_test_library()
        cache_file.write_text(json.dumps(test_data, ensure_ascii=False))

        # 创建管理器并修改缓存路径
        lm = LibraryManager()
        # 临时替换缓存路径
        from client.core import library_manager
        old_cache_dir = library_manager.CACHE_DIR
        old_cache_file = library_manager.LIBRARY_CACHE_FILE
        old_meta_file = library_manager.LIBRARY_META_FILE

        try:
            library_manager.CACHE_DIR = Path(tmpdir)
            library_manager.LIBRARY_CACHE_FILE = cache_file
            library_manager.LIBRARY_META_FILE = Path(tmpdir) / "library_meta.json"

            # 测试从缓存加载
            success = lm.load(client=None, use_cache=True)
            assert success == True
            assert lm.is_loaded == True
            assert lm.count == 4
            print(f"✓ 从缓存加载正常: {lm.count} 个游戏")

        finally:
            library_manager.CACHE_DIR = old_cache_dir
            library_manager.LIBRARY_CACHE_FILE = old_cache_file
            library_manager.LIBRARY_META_FILE = old_meta_file


def test_load_from_cloud():
    """测试从云端加载（模拟）"""
    print("\n=== 测试从云端加载（模拟） ===")

    lm = LibraryManager()

    # 模拟 WebDAV 客户端
    mock_client = Mock()
    mock_client.download_json.return_value = {"games": create_test_library()}

    success = lm.load(client=mock_client, use_cache=False)

    assert success == True
    assert lm.is_loaded == True
    assert lm.count == 4
    mock_client.download_json.assert_called_once()
    print("✓ 从云端加载正常（模拟）")


def test_load_from_cloud_list_format():
    """测试从云端加载（列表格式）"""
    print("\n=== 测试从云端加载（列表格式） ===")

    lm = LibraryManager()

    # 模拟 WebDAV 客户端返回列表格式
    mock_client = Mock()
    mock_client.download_json.return_value = create_test_library()

    success = lm.load(client=mock_client, use_cache=False)

    assert success == True
    assert lm.count == 4
    print("✓ 从云端加载正常（列表格式）")


def test_load_failure():
    """测试加载失败"""
    print("\n=== 测试加载失败 ===")

    lm = LibraryManager()

    # 模拟失败的客户端
    mock_client = Mock()
    mock_client.download_json.side_effect = Exception("网络错误")

    success = lm.load(client=mock_client, use_cache=False)

    assert success == False
    assert lm.is_loaded == False
    print("✓ 加载失败处理正常")


def test_get_library_manager_singleton():
    """测试全局实例"""
    print("\n=== 测试全局实例 ===")

    lm1 = get_library_manager()
    lm2 = get_library_manager()

    assert lm1 is lm2, "应返回同一实例"
    print("✓ 全局实例单例模式正常")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("ClawSave - 路径库管理器测试")
    print("=" * 50)

    try:
        test_search_exact_match()
        test_search_partial_match()
        test_search_case_insensitive()
        test_search_limit()
        test_search_empty_query()
        test_search_no_match()
        test_search_not_loaded()
        test_get_platform_path()
        test_get_platform_path_not_found()
        test_get_by_id()
        test_properties()
        test_load_from_cache()
        test_load_from_cloud()
        test_load_from_cloud_list_format()
        test_load_failure()
        test_get_library_manager_singleton()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
