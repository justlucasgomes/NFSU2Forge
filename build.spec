# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for NFS2Forge
# Run: pyinstaller build.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets',  'assets'),
        ('presets', 'presets'),
        ('img',     'img'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NFS2Forge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window
    icon='img/app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NFS2Forge',
)
