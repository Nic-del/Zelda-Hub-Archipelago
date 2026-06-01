# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\assets', 'assets'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\controller', 'controller'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\clipboard_paste.ps1', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\maximize_poptracker.ps1', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\minimize_lua_console.ps1', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\send_input.ps1', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\games_metadata.json', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\center_broadcast.ps1', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\web_tracker_host.py', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\ui_controller.py', '.'), ('C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\ui_setup.py', '.'), ('C:\\Users\\Linksweld\\AppData\\Roaming\\Python\\Python314\\site-packages\\customtkinter', 'customtkinter')]
binaries = []
hiddenimports = ['pygame', 'psutil', 'keyboard', 'customtkinter', 'PIL', 'win32gui', 'win32process', 'win32con', 'obswebsocket', 'controller_manager', 'device_detector', 'profile_manager', 'input_mapper', 'config_exporter']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pygame')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\ui_main.py'],
    pathex=['C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src', 'C:\\Users\\Linksweld\\Documents\\Folder Git\\Zelda Hub\\python_src\\controller'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='ZeldaMultiLauncherHub',
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
