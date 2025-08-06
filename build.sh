#!/usr/bin/env bash
# exit on error
set -o errexit

# Install MeCab system dependencies
echo "Installing MeCab system dependencies..."
apt-get update -qq
apt-get install -y mecab mecab-ko mecab-ko-dic mecab-utils

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Verify MeCab installation
echo "Verifying MeCab installation..."
mecab --version
echo "안녕하세요" | mecab

python manage.py collectstatic --no-input
python manage.py migrate --run-syncdb 