#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install MeCab using alternative methods
echo "Installing MeCab..."
python download_mecab.py

python manage.py collectstatic --no-input
python manage.py migrate --run-syncdb 