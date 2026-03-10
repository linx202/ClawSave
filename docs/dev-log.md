# ClawSave 开发日志

> 最后更新：2026-03-10

---

## 开发进度总览

| 阶段 | 状态 | 说明 |
|------|------|------|
| P0 核心闭环 | ✅ 完成 | file_handler, config_manager, meta_manager, webdav_client |
| P1 GUI 界面 | ✅ 完成 | 主窗口、对话框、自定义组件、CLI 备选 |
| P2 进阶功能 | ⬜ 待开始 | - |

---

## P0 核心模块开发总结

> 开发日期：2026-03-09
> 开发阶段：Phase 0 - 核心闭环（MVP）

## 1. 开发目标

实现 ClawSave 客户端的核心功能闭环，使"添加游戏 → 备份存档 → 恢复存档"主流程可以跑通。

## 2. 已完成模块

### 2.1 文件处理层 (`core/file_handler.py`)

负责本地文件的路径解析、压缩和解压操作。

| 函数 | 功能 |
|------|------|
| `expand_path(path)` | 解析环境变量路径（支持 `%APPDATA%`、`$HOME` 等） |
| `pack_directory(src_dir, dest_zip)` | 将目录打包为 zip 文件 |
| `unpack_archive(zip_path, dest_dir)` | 解压 zip 到指定目录 |
| `generate_archive_filename()` | 生成存档文件名（`YYYY-MM-DD_HH-MM-SS.zip`） |
| `get_directory_size(path)` | 计算目录大小 |

**实现要点：**
- 使用 `os.path.expandvars` 处理跨平台环境变量
- 使用 Python 标准库 `zipfile` 进行压缩
- 包含路径遍历攻击防护

---

### 2.2 配置管理 (`core/config_manager.py`)

负责本地 `config.json` 的读写操作，包括游戏配置的 CRUD 和唯一性校验。

| 方法 | 功能 |
|------|------|
| `load()` / `save()` | 加载/保存配置文件 |
| `set_user()` | 设置 WebDAV 连接信息 |
| `get_password()` | 从密钥环获取密码 |
| `is_user_configured()` | 检查用户是否已配置 |
| `generate_game_id()` | 生成游戏 ID（`game_YYMMDD_HHMMSS`） |
| `is_name_unique(name)` | 检查游戏名称唯一性（忽略大小写） |
| `add_game()` / `update_game()` / `remove_game()` | 游戏 CRUD 操作 |

**数据结构（config.json）：**
```json
{
  "config_version": "1.0",
  "user": {
    "username": "admin",
    "webdav_url": "http://..."
  },
  "games": [
    {
      "id": "game_260309_153022",
      "name": "塞尔达传说",
      "local_path": "%APPDATA%\\GamePath",
      "source": "manual",
      "last_sync": "2026-03-09T15:30:22"
    }
  ]
}
```

**注意：** 密码不存储在配置文件中，而是使用系统密钥环安全存储。

---

### 2.3 凭证管理 (`core/credential_manager.py`)

使用系统密钥环安全存储 WebDAV 密码。

| 函数 | 功能 |
|------|------|
| `save_password(username, password)` | 保存密码到密钥环 |
| `get_password(username)` | 从密钥环获取密码 |
| `delete_password(username)` | 删除密码 |
| `has_password(username)` | 检查密码是否存在 |
| `is_keyring_available()` | 检查密钥环是否可用 |

**跨平台支持：**
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service (GNOME Keyring / KWallet)

---

### 2.4 元数据管理 (`core/meta_manager.py`)

负责云端 `meta.json` 的读写操作，管理存档备份记录和备注。

| 函数 | 功能 |
|------|------|
| `create_meta(game_name)` | 创建初始元数据 |
| `add_backup(meta, filename, note)` | 添加备份记录 |
| `list_backups(meta)` | 列出备份（按时间倒序） |
| `get_note()` / `set_note()` | 获取/设置备注 |
| `remove_backup(meta, filename)` | 移除备份记录 |
| `to_json()` / `from_json()` | JSON 序列化/反序列化 |

**数据结构（meta.json）：**
```json
{
  "game_name": "塞尔达传说",
  "latest_backup": "2026-03-09_15-30-22.zip",
  "notes": {
    "2026-03-09_15-30-22.zip": "打完四神",
    "2026-03-09_12-00-00.zip": "初始备份"
  }
}
```

---

### 2.5 WebDAV 客户端 (`core/webdav_client.py`)

封装 WebDAV 协议操作，支持目录创建、文件上传下载、列表查询等。

| 方法 | 功能 |
|------|------|
| `test_connection()` | 测试连接是否正常 |
| `mkdir(path)` | 创建目录（支持递归） |
| `upload(local_path, remote_path)` | 上传文件 |
| `download(remote_path, local_path)` | 下载文件 |
| `list_dir(remote_path)` | 列出目录内容 |
| `delete(remote_path)` | 删除文件/目录 |
| `exists(remote_path)` | 检查是否存在 |
| `upload_json()` / `download_json()` | JSON 文件上传/下载 |

**实现要点：**
- 使用 `requests` 库实现，支持 Basic 和 Digest 认证
- 默认使用 Digest 认证（适配 Apache WebDAV）
- 目录路径必须以 `/` 结尾（服务器要求）
- 支持进度回调

---

### 2.6 辅助工具

| 文件 | 功能 |
|------|------|
| `setup_credentials.py` | 交互式凭证设置工具 |
| `test_core.py` | 单元测试（file_handler, config_manager, meta_manager） |
| `test_webdav.py` | WebDAV 集成测试 |

---

## 3. 依赖项

```
# client/requirements.txt
customtkinter>=5.2.0    # GUI 框架
requests>=2.31.0        # HTTP 客户端
webdavclient3>=3.2      # WebDAV 客户端（已替换为 requests 实现）
keyring>=24.0.0         # 系统密钥环
```

---

## 4. 技术决策记录

### 4.1 密码存储方案

**问题：** 原设计在 `config.json` 中明文存储密码，存在安全风险。

**解决方案：** 使用系统密钥环（keyring）存储密码，配置文件只存储用户名和 URL。

**优点：**
- 密码不会意外泄露（如配置文件被分享）
- 利用操作系统级安全机制
- 支持旧密码自动迁移

---

### 4.2 WebDAV 认证方式

**问题：** 初始实现使用 `webdavclient3` 库，但对 Digest 认证支持不佳，导致 401 错误。

**解决方案：** 使用 `requests` 库重新实现 WebDAV 客户端，显式支持 Digest 认证。

**要点：**
- 服务器使用 Apache WebDAV，默认 Digest 认证
- 目录路径必须以 `/` 结尾，否则返回 400 错误

---

### 4.3 压缩/解压位置

**决策：** 压缩和解压操作都在**客户端**完成，服务端只存储 `.zip` 文件。

**优点：**
- 服务端简单，只做文件存储
- 跨平台兼容性好
- 带宽优化（压缩后传输）

---

## 5. 测试验证

### 5.1 单元测试

```bash
python3 -m client.test_core
```

测试覆盖：
- ✅ 路径解析（环境变量展开）
- ✅ 目录压缩/解压
- ✅ 配置读写
- ✅ 名称唯一性校验
- ✅ ID 生成格式
- ✅ 元数据 CRUD
- ✅ 密钥环操作

### 5.2 集成测试

```bash
python3 -m client.test_webdav
```

测试覆盖：
- ✅ WebDAV 连接
- ✅ 目录创建
- ✅ 存档上传
- ✅ 存档下载
- ✅ 目录列表
- ✅ 元数据上传/下载

---

## 6. 已知问题

| 问题 | 状态 | 说明 |
|------|------|------|
| 删除非空目录失败 | 待优化 | 服务器可能不支持递归删除，需先清空子目录 |
| ~~GUI 在 macOS 26 无法启动~~ | ✅ 已解决 | 2026-03-10 修复 |

---

# P1 GUI 界面开发总结

> 开发日期：2026-03-09
> 开发阶段：Phase 1 - 用户体验

## 1. 已完成模块

### 1.1 主窗口 (`ui/main_window.py`)

**类**: `MainWindow`

**功能**:
- 游戏列表展示（滚动区域）
- 连接状态显示
- 备份/恢复操作（后台线程）
- 状态栏反馈

### 1.2 对话框 (`ui/dialogs.py`)

| 对话框 | 功能 |
|--------|------|
| `AddGameDialog` | 添加游戏（名称唯一性校验、路径浏览） |
| `SettingsDialog` | WebDAV 配置、连接测试 |
| `RestoreDialog` | 存档版本选择（从云端加载列表） |

### 1.3 自定义组件 (`ui/widgets.py`)

| 组件 | 功能 |
|------|------|
| `GameCard` | 游戏卡片（名称、路径、同步时间、操作按钮） |
| `StatusBar` | 状态栏（文本 + 进度条） |
| `EmptyState` | 空列表占位 |

### 1.4 命令行版本 (`cli.py`)

当 GUI 不可用时的备选方案，支持：
- 游戏列表/添加
- 备份/恢复
- 设置配置

## 2. 技术要点

### 2.1 线程处理

网络操作在后台线程执行，使用 `self.after()` 回调更新 UI：

```python
def backup_task():
    # 后台执行
    self.after(0, callback)

thread = threading.Thread(target=backup_task, daemon=True)
thread.start()
```

### 2.2 依赖

```
customtkinter>=5.2.0  # GUI 框架
```

## 3. macOS 26 兼容性问题

**问题描述**:
- macOS 26 (Tahoe) 自带 Tcl/Tk 8.5.9
- 该版本与 macOS 26 不兼容，导致 Tk 初始化崩溃

**错误信息**:
```
macOS 26 (2602) or later required, have instead 16 (1602) !
Tcl_Panic
```

**解决方案**:
1. 安装官方 Python（自带新版 Tk）：https://www.python.org/downloads/macos/
2. 使用 CLI 版本：`python3 -m client.cli`

---

## 4. 文件结构（更新）

```
client/
├── main.py                     # GUI 入口
├── cli.py                      # CLI 入口（新增）
├── requirements.txt            # Python 依赖
├── setup_credentials.py        # 凭证设置工具
├── test_core.py               # 单元测试
├── test_webdav.py             # 集成测试
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # 主窗口 ✅
│   ├── dialogs.py             # 对话框 ✅
│   └── widgets.py             # 自定义组件 ✅
└── core/
    ├── __init__.py            # 模块导出
    ├── config_manager.py      # 配置管理
    ├── credential_manager.py  # 凭证管理
    ├── file_handler.py        # 文件处理
    ├── meta_manager.py        # 元数据管理
    └── webdav_client.py       # WebDAV 客户端
```

---

## 5. 下一步计划 (P2)

- [ ] 智能路径库（从云端拉取 games_library.json）
- [ ] 存档详情查看
- [ ] 异常处理优化（网络断开重试）
