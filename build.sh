#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies (including mecab-python3)
pip install -r requirements.txt

# Note: MeCab system dependencies are not available on this platform
# The application will use fallback Korean text analysis

python manage.py collectstatic --no-input
python manage.py migrate --run-syncdb 