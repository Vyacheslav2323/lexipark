#!/bin/bash

# Install MeCab with Korean support
echo "Installing MeCab with Korean support..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl git

# Install basic MeCab
apt-get install -y mecab mecab-utils

# Install Korean MeCab dictionary using git clone with depth 1
echo "Installing Korean MeCab dictionary..."
cd /tmp
git clone --depth 1 https://github.com/konlpy/mecab-ko-dic.git
cd mecab-ko-dic
./configure
make
make install

# Setup MeCab configuration for Korean
echo "Setting up MeCab configuration for Korean..."
mkdir -p /usr/local/etc
cat > /usr/local/etc/mecabrc << 'EOF'
dicdir = /usr/local/lib/mecab/dic/mecab-ko-dic
userdic = 
output-format-type = wakati
input-buffer-size = 8192
node-format = %m\n
bos-format = 
eos-format = \n
eos-format = \n
EOF

# Test MeCab installation
echo "Testing MeCab installation..."
mecab --version

# Test with Korean text
echo "Testing Korean text analysis..."
echo "안녕하세요" | mecab

echo "MeCab installation completed!" 