#!/bin/bash

# Install MeCab with Korean support
echo "Installing MeCab with Korean support..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl

# Install basic MeCab
apt-get install -y mecab mecab-utils mecab-ipadic-utf8

# Test MeCab installation
echo "Testing MeCab installation..."
mecab --version

# Test with Korean text
echo "Testing Korean text analysis..."
echo "안녕하세요" | mecab

echo "MeCab installation completed!" 