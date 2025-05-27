#!/bin/bash

echo "========================================"
echo " Cimbar Decoder - 彩色图形矩阵条形码解码器"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8或更高版本"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "错误: Python版本过低，需要3.8或更高版本"
    echo "当前版本: $PYTHON_VERSION"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 检查依赖是否已安装
if ! python -c "import cv2, mss, PIL" &> /dev/null; then
    echo "安装依赖包..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

# 检查cimbar可执行文件
CIMBAR_FOUND=false

if [ -f "./cimbar" ]; then
    CIMBAR_FOUND=true
elif [ -f "../build/cimbar" ]; then
    CIMBAR_FOUND=true
elif command -v cimbar &> /dev/null; then
    CIMBAR_FOUND=true
fi

if [ "$CIMBAR_FOUND" = false ]; then
    echo "警告: 未找到cimbar可执行文件"
    echo "请确保已编译libcimbar项目"
    echo "编译方法:"
    echo "  cd .."
    echo "  mkdir build && cd build"
    echo "  cmake .."
    echo "  make"
    echo
fi

# 确保脚本有执行权限
if [ -f "./cimbar" ] && [ ! -x "./cimbar" ]; then
    echo "添加cimbar执行权限..."
    chmod +x ./cimbar
fi

# 启动解码器
echo "正在启动Cimbar解码器..."
python cimbar_decoder.py

# 检查退出状态
if [ $? -ne 0 ]; then
    echo
    echo "程序异常退出"
    read -p "按回车键退出..."
fi

# 退出虚拟环境
deactivate