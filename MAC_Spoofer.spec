# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Squir\\Desktop\\MAC-SPOOFER-main\\mac_spoofer_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Squir\\Desktop\\MAC-SPOOFER-main\\README.md', '.'), ('C:\\Users\\Squir\\Desktop\\MAC-SPOOFER-main\\LICENSE', '.'), ('C:\\Users\\Squir\\Desktop\\MAC-SPOOFER-main\\version.md', '.'), ('C:\\Users\\Squir\\Desktop\\MAC-SPOOFER-main\\asset.PNG', '.')],
    hiddenimports=[],
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
    name='MAC_Spoofer',
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
)
