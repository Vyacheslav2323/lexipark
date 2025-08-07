#!/bin/bash

# Install MeCab Korean from source
echo "Installing MeCab Korean..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl

# Download and install MeCab Korean from GitHub
cd /tmp
curl -L https://github.com/konlpy/mecab-ko/archive/refs/heads/master.tar.gz -o mecab-ko.tar.gz
tar -xzf mecab-ko.tar.gz
cd mecab-ko-master
./configure
make
make install

# Download and install MeCab Korean dictionary from GitHub
cd /tmp
curl -L https://github.com/konlpy/mecab-ko-dic/archive/refs/heads/master.tar.gz -o mecab-ko-dic.tar.gz
tar -xzf mecab-ko-dic.tar.gz
cd mecab-ko-dic-master
./configure
make
make install

# Update library path
echo "/usr/local/lib" > /etc/ld.so.conf.d/mecab.conf
ldconfig

echo "MeCab Korean installation completed!"
