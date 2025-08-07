#!/bin/bash

set -e  # Exit on any error

echo "Installing MeCab and Korean dictionary using package manager..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl git autoconf automake libtool pkg-config

# Try to install MeCab and Korean dictionary via package manager
echo "Attempting package manager installation..."
if apt-get install -y mecab mecab-utils mecab-ko mecab-ko-dic 2>/dev/null; then
    echo "✅ MeCab and Korean dictionary installed via package manager"
else
    echo "⚠️  Package manager installation failed, trying source compilation..."
    
    # Install MeCab from official source
    cd /tmp
    wget https://github.com/taku910/mecab/archive/refs/tags/v0.996.tar.gz
    tar -xzf v0.996.tar.gz
    cd mecab-0.996
    ./configure
    make -j$(nproc)
    make install

    # Try to install Korean dictionary from package manager first
    if apt-get install -y mecab-ko-dic 2>/dev/null; then
        echo "✅ Korean dictionary installed via package manager"
    else
        echo "⚠️  Korean dictionary not available via package manager, trying alternative sources..."
        
        # Try alternative Korean dictionary sources
        cd /tmp
        
        # Try to download from a different source
        if wget -O mecab-ko-dic.tar.gz "https://github.com/konlpy/mecab-ko-dic/archive/refs/heads/master.tar.gz" 2>/dev/null; then
            tar -xzf mecab-ko-dic.tar.gz
            cd mecab-ko-dic-master
            ./autogen.sh
            ./configure --with-dicdir=/usr/local/lib/mecab/dic
            make -j$(nproc)
            make install
        else
            echo "❌ Could not download Korean dictionary. Please install manually:"
            echo "   sudo apt-get install mecab-ko-dic"
            echo "   or download from: https://bitbucket.org/eunjeon/mecab-ko-dic"
            exit 1
        fi
    fi
fi

# Find the correct dictionary path
DIC_PATH=""
for path in "/usr/local/lib/mecab/dic/mecab-ko-dic" "/usr/lib/mecab/dic/mecab-ko-dic" "/opt/homebrew/lib/mecab/dic/mecab-ko-dic"; do
    if [ -d "$path" ]; then
        DIC_PATH="$path"
        break
    fi
done

if [ -z "$DIC_PATH" ]; then
    echo "⚠️  Could not find Korean dictionary path automatically"
    echo "   Trying to find it..."
    DIC_PATH=$(find /usr -name "mecab-ko-dic" -type d 2>/dev/null | head -1)
    if [ -z "$DIC_PATH" ]; then
        echo "❌ Could not find Korean dictionary. Please check installation."
        exit 1
    fi
fi

echo "✅ Found Korean dictionary at: $DIC_PATH"

# Set up mecabrc
cat > /usr/local/etc/mecabrc << EOF
dicdir = $DIC_PATH
EOF

# Add MeCab to PATH if needed
ldconfig

# Test MeCab
echo "Testing MeCab version..."
mecab --version

echo "Testing Korean tokenization..."
echo "안녕하세요. 만나서 반갑습니다." | mecab

echo "✅ MeCab installation completed successfully!"
