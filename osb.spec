# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

datas = []
if os.path.exists('assets'):
    datas.append(('assets', 'assets'))

a = Analysis(
    ['osb/main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'osb',
        'osb.core',
        'osb.core.config_mgr',
        'osb.core.constants',
        'osb.core.logger',
        'osb.core.models',
        'osb.core.rclone_cli',
        'osb.core.rclone_detector',
        'osb.core.transfer_mgr',
        'osb.core.utils',
        'osb.gui',
        'osb.gui.bucket_dialog',
        'osb.gui.dual_panel',
        'osb.gui.jobs_view',
        'osb.gui.log_dialog',
        'osb.gui.main_window',
        'osb.gui.outline_icons',
        'osb.gui.panel_browser',
        'osb.gui.rclone_dialog',
        'osb.gui.remote_dialog',
        'osb.gui.theme',
    ],
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

app_icon = None
if sys.platform == 'win32' and os.path.exists('assets/icon.ico'):
    app_icon = 'assets/icon.ico'
elif os.path.exists('assets/icon.png'):
    app_icon = 'assets/icon.png'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OSB' if sys.platform == 'win32' else 'osb',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='OSB.app',
        icon='assets/icon.png',
        bundle_identifier='com.bdata.osb',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
        },
    )
