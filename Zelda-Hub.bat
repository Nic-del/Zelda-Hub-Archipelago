@echo off
cd /d "%~dp0python_src"
echo [Launcher] Verification des dependances...
py -3.12 -m pip install -r requirements.txt --quiet
start "" py -3.12 ui_main.py
exit
