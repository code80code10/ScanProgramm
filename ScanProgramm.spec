# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('tesseract', 'tesseract'), ('config.json', '.')],
    hiddenimports=['pytesseract', 'fitz', 'PIL', 'watchdog', 'fuzzywuzzy', 'fuzzywuzzy.fuzz', 'fuzzywuzzy.process', 'Levenshtein', 'main_window', 'paths', 'setup_window', 'gui', 'notifier', 'renamer', 'memory', 'parser', 'ocr_engine', 'config', 'watcher'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ScanProgramm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
