@echo off
chcp 65001 >nul
echo ============================================
echo        论文知识图谱系统 - Windows启动脚本
echo ============================================
echo 正在启动系统...
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [检查] Python环境 - OK

REM 检查并创建虚拟环境
if not exist "venv" (
    echo [创建] 虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
)

echo [检查] 虚拟环境 - OK

REM 激活虚拟环境
echo [激活] 虚拟环境...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)

REM 升级pip
echo [更新] pip包管理器...
python -m pip install --upgrade pip >nul 2>&1

REM 安装依赖
echo [安装] 项目依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖包安装失败，请检查网络连接
    pause
    exit /b 1
)

echo [检查] 依赖安装 - OK

REM 确保数据目录存在
if not exist "data" mkdir data
if not exist "data\papers" mkdir data\papers
if not exist "data\graph" mkdir data\graph

echo [检查] 数据目录 - OK

REM 启动提示
echo.
echo ============================================
echo 系统启动中...
echo 访问地址: http://localhost:5000
echo 首次使用请先进入"系统设置"配置OpenAI API
echo.
echo 按 Ctrl+C 可停止服务
echo ============================================
echo.

REM 启动Flask应用
python app.py

REM 如果意外退出，暂停以查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo [错误] 应用启动失败，错误代码: %errorlevel%
    pause
) 