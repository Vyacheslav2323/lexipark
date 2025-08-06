#!/usr/bin/env python3
"""
Download pre-compiled MeCab binaries for deployment
"""
import os
import sys
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path

def download_mecab_binaries():
    """Download pre-compiled MeCab binaries"""
    print("Downloading MeCab binaries...")
    
    # Create mecab directory
    mecab_dir = Path("mecab_bin")
    mecab_dir.mkdir(exist_ok=True)
    
    # Download URLs for pre-compiled MeCab (these would need to be actual URLs)
    # For now, we'll try to install via conda-forge which often works on deployment platforms
    
    try:
        # Try conda installation
        subprocess.run(['conda', 'install', '-c', 'conda-forge', 'mecab', 'mecab-ko', 'mecab-ko-dic', '-y'], check=True)
        print("MeCab installed via conda-forge!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Conda installation failed, trying pip...")
        
        try:
            # Try pip installation with specific versions
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'mecab-python3==1.0.10'], check=True)
            print("MeCab installed via pip!")
            return True
        except subprocess.CalledProcessError:
            print("Pip installation failed")
            return False

if __name__ == "__main__":
    success = download_mecab_binaries()
    if success:
        print("MeCab installation completed!")
    else:
        print("MeCab installation failed")
        sys.exit(1) 