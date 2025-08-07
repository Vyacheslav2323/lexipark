#!/bin/bash

set -e  # Exit on any error

echo "Installing MeCab with Korean support using package manager..."

# Detect OS and install accordingly
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    apt-get update
    apt-get install -y mecab mecab-utils mecab-ko mecab-ko-dic
    
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    yum install -y mecab mecab-utils mecab-ko mecab-ko-dic
    
elif command -v brew &> /dev/null; then
    # macOS
    brew install mecab mecab-ko mecab-ko-dic
    
else
    echo "❌ Unsupported package manager. Please install MeCab manually."
    exit 1
fi

# Set up mecabrc if it doesn't exist
if [ ! -f /usr/local/etc/mecabrc ] && [ ! -f /etc/mecabrc ]; then
    cat > /usr/local/etc/mecabrc << EOF
dicdir = /usr/local/lib/mecab/dic/mecab-ko-dic
EOF
fi

# Update library cache
ldconfig

# Test MeCab
echo "Testing MeCab version..."
mecab --version

echo "Testing Korean tokenization..."
echo "안녕하세요. 만나서 반갑습니다." | mecab

echo "✅ MeCab installation completed successfully!" 