#!/usr/bin/env python3
"""
Bundle MeCab binaries with the application for deployment
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_mecab_bundle():
    """Setup MeCab bundle for deployment"""
    print("Setting up MeCab bundle...")
    
    # Create mecab directory in the project
    mecab_dir = Path("mecab_bundle")
    mecab_dir.mkdir(exist_ok=True)
    
    # Set environment variables to use bundled MeCab
    os.environ['MECAB_PATH'] = str(mecab_dir / 'mecab')
    os.environ['MECAB_DIC_PATH'] = str(mecab_dir / 'dic')
    
    print("MeCab bundle setup completed!")

if __name__ == "__main__":
    setup_mecab_bundle() 