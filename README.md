# ClawSave

[中文](#中文) | [English](#english)

---

<a name="中文"></a>

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
python main.py  # 或使用 CLI: python cli.py
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

---

<a name="english"></a>

A lightweight private cloud save sync tool for gamers.

## Features

- **Self-hosted** - Your saves stay on your own server
- **Cross-platform** - Windows / macOS / Linux support
- **Version Control** - Auto-archive with timestamps
- **Easy Deploy** - Docker + WebDAV, one command to start

## Quick Start

### Server

```bash
cd server
cp .env.example .env
# Edit .env to set username and password
docker-compose up -d
```

### Client

```bash
cd client
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py  # Or use CLI: python cli.py
```

## Project Structure

```
ClawSave/
├── client/     # Python client (CustomTkinter)
├── server/     # Server (Docker + WebDAV)
└── docs/       # Documentation
```

## Tech Stack

| Module | Tech |
|--------|------|
| Client | Python 3.10+, CustomTkinter |
| Server | Docker, WebDAV |
| Network | Tailscale (optional) |

## License

MIT
