# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all

# On détecte automatiquement le dossier du projet (là où se trouve ce fichier .spec)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))
PYTHON_SRC = os.path.join(PROJECT_ROOT, 'python_src')

# Détection dynamique de customtkinter pour plus de portabilité
try:
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
except ImportError:
    ctk_path = ""

datas = [
    (os.path.join(PYTHON_SRC, 'assets'), 'assets'), 
    (os.path.join(PYTHON_SRC, 'controller'), 'controller'), 
    (os.path.join(PYTHON_SRC, 'clipboard_paste.ps1'), '.'), 
    (os.path.join(PYTHON_SRC, 'maximize_poptracker.ps1'), '.'), 
    (os.path.join(PYTHON_SRC, 'minimize_lua_console.ps1'), '.'), 
    (os.path.join(PYTHON_SRC, 'send_input.ps1'), '.'), 
    (os.path.join(PYTHON_SRC, 'games_metadata.json'), '.'), 
    (os.path.join(PYTHON_SRC, 'center_broadcast.ps1'), '.'), 
    (os.path.join(PYTHON_SRC, 'web_tracker_host.py'), '.'), 
    (os.path.join(PYTHON_SRC, 'ui_controller.py'), '.'), 
    (os.path.join(PYTHON_SRC, 'ui_setup.py'), '.'), 
]

if ctk_path:
    datas.append((ctk_path, 'customtkinter'))
binaries = []
hiddenimports = ['pygame', 'psutil', 'keyboard', 'customtkinter', 'PIL', 'win32gui', 'win32process', 'win32con', 'obswebsocket', 'controller_manager', 'device_detector', 'profile_manager', 'input_mapper', 'config_exporter']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pygame')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    [os.path.join(PYTHON_SRC, 'ui_main.py')],
    pathex=[PYTHON_SRC, os.path.join(PYTHON_SRC, 'controller')],
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
