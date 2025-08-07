#!/bin/bash

set -e  # Exit on any error

echo "Installing MeCab-ko and mecab-ko-dic for Korean..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl git autoconf automake libtool pkg-config

# Install MeCab-ko (Korean fork of MeCab)
cd /tmp
git clone --depth 1 https://github.com/konlpy/mecab-ko.git
cd mecab-ko
./autogen.sh
./configure
make -j$(nproc)
make install

# Install mecab-ko-dic (Korean dictionary)
cd /tmp
git clone --depth 1 https://github.com/konlpy/mecab-ko-dic.git
cd mecab-ko-dic
./autogen.sh
./configure --with-dicdir=/usr/local/lib/mecab/dic
make -j$(nproc)
make install

# Set up mecabrc
cat > /usr/local/etc/mecabrc << EOF
dicdir = /usr/local/lib/mecab/dic/mecab-ko-dic
EOF

# Add MeCab to PATH if needed
ldconfig

# Test MeCab
echo "Testing MeCab version..."
mecab --version

echo "Testing Korean tokenization..."
echo "안녕하세요. 만나서 반갑습니다." | mecab

echo "✅ MeCab-ko installation completed successfully!"
