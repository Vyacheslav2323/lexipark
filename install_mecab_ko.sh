#!/bin/bash

# Install MeCab Korean from source
echo "Installing MeCab Korean..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl

# Download and install MeCab Korean
cd /tmp
curl -L -O https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-ko-1.2.0.tar.gz
tar -xzf mecab-ko-1.2.0.tar.gz
cd mecab-ko-1.2.0
./configure
make
make install

# Download and install MeCab Korean dictionary
cd /tmp
curl -L -O https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz
tar -xzf mecab-ko-dic-2.1.1-20180720.tar.gz
cd mecab-ko-dic-2.1.1-20180720
./configure
make
make install

# Update library path
echo "/usr/local/lib" > /etc/ld.so.conf.d/mecab.conf
ldconfig

echo "MeCab Korean installation completed!" 