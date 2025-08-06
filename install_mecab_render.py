#!/usr/bin/env python3
"""
Install MeCab on Render using alternative methods
"""
import os
import sys
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path

def install_mecab_on_render():
    """Install MeCab on Render using alternative methods"""
    print("Installing MeCab on Render...")
    
    # Method 1: Try to install via conda (if available)
    try:
        subprocess.run(['conda', 'install', '-c', 'conda-forge', 'mecab', 'mecab-ko', 'mecab-ko-dic', '-y'], check=True)
        print("MeCab installed via conda!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Conda not available, trying alternative method...")
    
    # Method 2: Try to install via pip with system packages
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'mecab-python3', 'mecab-ko'], check=True)
        print("MeCab installed via pip!")
        return True
    except subprocess.CalledProcessError:
        print("Pip installation failed...")
    
    # Method 3: Download and compile MeCab manually
    try:
        print("Attempting manual MeCab installation...")
        # This would require downloading and compiling MeCab
        # For now, we'll use a different approach
        return False
    except Exception as e:
        print(f"Manual installation failed: {e}")
        return False

if __name__ == "__main__":
    success = install_mecab_on_render()
    if success:
        print("MeCab installation completed successfully!")
    else:
        print("MeCab installation failed - will use fallback") 