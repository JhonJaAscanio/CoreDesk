# -*- mode: python ; coding: utf-8 -*-
# Se genera en formato carpeta (dist/CoreDesk/): el formato de un solo archivo descomprime
# Qt WebEngine en cada arranque y tarda unas cuatro veces más en abrir.

# Comprimir los binarios de Qt WebEngine con UPX los corrompe
UPX_EXCLUDE = ['Qt6WebEngineCore.dll', 'QtWebEngineProcess.exe', 'Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll']

a = Analysis(
    ['CoreDesk.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CoreDesk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=UPX_EXCLUDE,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=UPX_EXCLUDE,
    name='CoreDesk',
)
