@echo off
title Zelda Hub Patcher Launcher
echo Launching Zelda Hub Patcher using Python 3.12 with optimizations...
py -3.12 -O ZeldaHubPatcher.py
if %errorlevel% neq 0 (
    echo.
    echo Something went wrong. Make sure Python 3.12 is installed correctly.
    pause
)
