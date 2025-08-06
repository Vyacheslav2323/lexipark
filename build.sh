#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for MeCab
apt-get update -qq
apt-get install -y mecab mecab-ko mecab-ko-dic mecab-utils

# Install Python dependencies
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --run-syncdb 