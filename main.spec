# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],       # 1. 确保这里是你的主程序文件名
    pathex=[],
    binaries=[],
    datas=[('name.png', '.')], # 2. 关键：把 name.png 作为一个资源文件打包进 EXE 内部
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PythonPackerPro',    # 3. 生成的软件名字
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                  # 开启压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,             # 4. 关键：False = 隐藏黑窗口 (无控制台)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='name.png',           # 5. 关键：设置 EXE 文件本身的图标
)