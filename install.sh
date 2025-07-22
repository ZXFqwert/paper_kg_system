#!/bin/bash

echo "=================================================="
echo "📚 论文知识图谱系统安装脚本"
echo "=================================================="

# 检查Python版本
echo "🔍 检查Python环境..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [ $? -eq 0 ]; then
    echo "✓ 发现Python版本: $python_version"
else
    echo "❌ 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查pip
echo "🔍 检查pip..."
if command -v pip3 &> /dev/null; then
    echo "✓ pip3 已安装"
else
    echo "❌ 未找到pip3，请先安装pip"
    exit 1
fi

# 创建虚拟环境（可选）
echo ""
read -p "是否创建Python虚拟环境？(推荐) [y/N]: " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv paper_kg_env
    source paper_kg_env/bin/activate
    echo "✓ 虚拟环境已创建并激活"
    echo "💡 后续使用时请先运行: source paper_kg_env/bin/activate"
fi

# 安装依赖
echo "📥 安装Python依赖..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p data/papers data/graph static/css static/js templates
echo "✓ 目录创建完成"

# 运行演示初始化
echo "🎯 初始化演示环境..."
python3 demo.py

echo ""
echo "=================================================="
echo "🎉 安装完成！"
echo "=================================================="
echo ""
echo "🚀 启动命令:"
echo "   python3 run.py"
echo ""
echo "🌐 访问地址:"
echo "   http://localhost:5000"
echo ""
echo "📖 更多信息请查看 README.md"
echo "==================================================" 