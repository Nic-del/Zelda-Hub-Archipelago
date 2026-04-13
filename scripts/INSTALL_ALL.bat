@echo off
setlocal enabledelayedexpansion

echo ===========================================================
echo   INSTALLATION COMPLETE : LAUNCHER + UI BROADCAST
echo ===========================================================
echo.

:: 1. Installation des dépendances du Launcher (Python)
echo [1/2] Installation des dependances du Launcher...
if exist "INSTALL_LAUNCHER_DEPS.bat" (
    call INSTALL_LAUNCHER_DEPS.bat
) else (
    echo [ERREUR] INSTALL_LAUNCHER_DEPS.bat non trouve a la racine.
)

echo.
echo -----------------------------------------------------------
echo.

:: 2. Installation de l'UI Broadcast (Node.js + Python Broadcast)
echo [2/2] Installation de l'UI Broadcast...
set BROADCAST_DIR=..\App\UiBroadCast-Archipelago

if exist "%BROADCAST_DIR%\INSTALLATION.bat" (
    pushd "%BROADCAST_DIR%"
    call INSTALLATION.bat
    popd
) else (
    echo [ERREUR] %BROADCAST_DIR%\INSTALLATION.bat non trouve.
)

echo.
echo ===========================================================
echo   TOUTES LES ETAPES SONT TERMINEES !
echo ===========================================================
echo.
pause
