# hook-babel.py

from PyInstaller.utils.hooks import collect_all

# Collect all files and modules from babel package
datas, binaries, hiddenimports = collect_all('babel')
