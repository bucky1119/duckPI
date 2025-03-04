#!/bin/bash

# 设置变量
KING_URL="./tools/Linux-king.tar.gz"
PLINK_URL="./tools/plink_linux_x86_64_20241022.zip"
BIN_DIR="./bin"
SRC_DIR="./src"

# 创建 bin 目录
mkdir -p $BIN_DIR

# 解压king
echo "正在解压 King..."
tar -zxvf $KING_URL -C $BIN_DIR

# 解压plink
echo "正在解压 Plink..."
unzip $PLINK_URL -d $BIN_DIR

# 确保plink和king是可执行的
chmod +x $BIN_DIR/king
chmod +x $BIN_DIR/plink

# 安装python依赖
echo "正在安装Python依赖..."
pip install -r requirements.txt

echo "安装完成！可以开始使用duckPI了！"

