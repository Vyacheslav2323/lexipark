#!/bin/bash
set -e
# Install MeCab Korean from source
echo "Installing MeCab Korean..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl autoconf automake libtool pkg-config

# Download and install MeCab Korean from GitHub
cd /tmp
curl -L -o mecab-ko.tar.gz https://codeload.github.com/konlpy/mecab-ko/tar.gz/refs/heads/master
tar -xzf mecab-ko.tar.gz
cd mecab-ko-master
./autogen.sh
./configure
make -j$(nproc)
make install

# Download and install MeCab Korean dictionary from GitHub
cd /tmp
curl -L -o mecab-ko-dic.tar.gz https://codeload.github.com/konlpy/mecab-ko-dic/tar.gz/refs/heads/master
tar -xzf mecab-ko-dic.tar.gz
cd mecab-ko-dic-master
./autogen.sh
./configure --with-dicdir=/usr/local/lib/mecab/dic
make -j$(nproc)
make install

# Update library path
echo "/usr/local/lib" > /etc/ld.so.conf.d/mecab.conf
ldconfig

cat > /usr/local/etc/mecabrc << EOF
dicdir = /usr/local/lib/mecab/dic/mecab-ko-dic
EOF

# Final test
echo "Testing installation..."
mecab --version
echo "안녕하세요. 만나서 반갑습니다." | mecab

echo "✅ MeCab Korean installation completed!"
