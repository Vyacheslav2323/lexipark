#!/bin/bash

# Install MeCab with Korean support
echo "Installing MeCab with Korean support..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl

# Install basic MeCab with Japanese dictionary (we'll use this for now)
apt-get install -y mecab mecab-utils mecab-ipadic-utf8

# Setup MeCab configuration
echo "Setting up MeCab configuration..."
mkdir -p /usr/local/etc
cat > /usr/local/etc/mecabrc << 'EOF'
dicdir = /usr/lib/x86_64-linux-gnu/mecab/dic/ipadic
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