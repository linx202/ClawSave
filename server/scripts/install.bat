@echo off
REM ClawSave Server - Windows 一键部署

echo === ClawSave Server Installer ===

REM 检查 Docker
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Docker is not installed
    exit /b 1
)

where docker-compose >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Docker Compose is not installed
    exit /b 1
)

REM 创建 .env 文件
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env to set your credentials
)

REM 初始化数据目录
echo Initializing data directory...
if not exist data\ClawSave\_system mkdir data\ClawSave\_system
if not exist data\ClawSave\public mkdir data\ClawSave\public
if not exist data\ClawSave\users mkdir data\ClawSave\users

REM 复制初始配置
if not exist data\ClawSave\_system\games_library.json (
    xcopy /E /I config\init_data data\ClawSave
)

REM 启动服务
echo Starting WebDAV service...
docker-compose up -d

echo === Installation Complete ===
echo WebDAV is running
pause
