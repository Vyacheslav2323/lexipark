#!/bin/bash

set -e  # Exit on any error

echo "Installing MeCab and Korean dictionary..."

# Install dependencies
apt-get update
apt-get install -y build-essential curl git autoconf automake libtool pkg-config

# Try to install MeCab and Korean dictionary via package manager
echo "Attempting package manager installation..."
if apt-get install -y mecab mecab-utils mecab-ko mecab-ko-dic 2>/dev/null; then
    echo "✅ MeCab and Korean dictionary installed via package manager"
else
    echo "⚠️  Package manager installation failed, trying alternative repositories..."
    
    # Try adding different repositories
    echo "deb http://ftp.debian.org/debian stretch main" >> /etc/apt/sources.list
    echo "deb http://ftp.debian.org/debian buster main" >> /etc/apt/sources.list
    apt-get update
    
    if apt-get install -y mecab mecab-utils mecab-ko mecab-ko-dic 2>/dev/null; then
        echo "✅ MeCab installed from alternative repository"
    else
        echo "⚠️  Alternative repositories failed, trying minimal installation..."
        
        # Try to install just the basic MeCab without Korean dictionary
        if apt-get install -y mecab mecab-utils 2>/dev/null; then
            echo "✅ Basic MeCab installed, will use default dictionary"
        else
            echo "❌ Could not install MeCab. Please check your package sources."
            exit 1
        fi
    fi
fi

# Find the correct dictionary path
DIC_PATH=""
for path in "/usr/local/lib/mecab/dic/mecab-ko-dic" "/usr/lib/mecab/dic/mecab-ko-dic" "/opt/homebrew/lib/mecab/dic/mecab-ko-dic" "/usr/share/mecab/dic/ipadic"; do
    if [ -d "$path" ]; then
        DIC_PATH="$path"
        break
    fi
done

if [ -z "$DIC_PATH" ]; then
    echo "⚠️  Could not find dictionary path automatically"
    echo "   Trying to find it..."
    DIC_PATH=$(find /usr -name "*mecab*dic*" -type d 2>/dev/null | head -1)
    if [ -z "$DIC_PATH" ]; then
        echo "❌ Could not find any MeCab dictionary. Please check installation."
        exit 1
    fi
fi

echo "✅ Found dictionary at: $DIC_PATH"

# Set up mecabrc
cat > /usr/local/etc/mecabrc << EOF
dicdir = $DIC_PATH
EOF

# Add MeCab to PATH if needed
ldconfig

# Test MeCab
echo "Testing MeCab version..."
mecab --version

echo "Testing text tokenization..."
echo "Hello world." | mecab

echo "✅ MeCab installation completed successfully!"
