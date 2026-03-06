# ClawSave

轻量级私有云存档同步工具，面向极客玩家。

## 功能特性

- **数据私有化** - 存档完全存储在你的服务器上
- **跨平台同步** - 支持 Windows / macOS / Linux
- **版本管理** - 自动按时间戳归档历史版本
- **简单部署** - Docker + WebDAV，一键启动

## 快速开始

### 服务端部署

```bash
cd server
cp .env.example .env
# 编辑 .env 修改用户名和密码
docker-compose up -d
```

### 客户端运行

```bash
cd client
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## 项目结构

```
ClawSave/
├── client/     # Python 客户端 (CustomTkinter)
├── server/     # 服务端 (Docker + WebDAV)
└── docs/       # 文档
```

## 技术栈

| 模块 | 技术 |
|------|------|
| 客户端 | Python 3.10+, CustomTkinter |
| 服务端 | Docker, WebDAV |
| 网络 | Tailscale (可选) |

## License

MIT
