#!/bin/bash

# 论文知识图谱系统启动脚本

echo "=== 论文知识图谱系统 ==="
echo "正在启动系统..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 确保数据目录存在
mkdir -p data/papers
mkdir -p data/graph

echo "启动Flask应用..."
echo "访问地址: http://localhost:5000"
echo "首次使用请先进入'系统设置'配置OpenAI API"
echo ""

# 启动应用
python app.py 