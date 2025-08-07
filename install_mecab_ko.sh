#!/bin/bash

set -e  # Exit on any error

echo "Installing MeCab and Korean dictionary using package manager..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl git autoconf automake libtool pkg-config

# Install MeCab and Korean dictionary via package manager
apt-get install -y mecab mecab-utils mecab-ko mecab-ko-dic

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
