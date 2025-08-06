#!/bin/bash

# Install MeCab and Korean dictionary on Ubuntu/Debian systems
echo "Installing MeCab and Korean dictionary..."

# Update package list
apt-get update -qq

# Install MeCab and Korean dictionary
apt-get install -y mecab mecab-ko mecab-ko-dic mecab-utils

# Verify installation
echo "Verifying MeCab installation..."
mecab --version

# Test Korean analysis
echo "Testing Korean text analysis..."
echo "안녕하세요" | mecab

echo "MeCab installation completed!" 