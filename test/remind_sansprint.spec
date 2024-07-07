# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['remind_sansprint.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('adding_vectore.py', '.'), 
        ('delete_imagedb.py', '.'), 
        ('ingestion.py', '.'), 
        ('pipeline_db.py', '.'), 
        ('record_photo.py', '.'), 
        ('Regular_database.py', '.'), 
        ('swift.py', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='remind_sansprint',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='remind_sansprint'
)