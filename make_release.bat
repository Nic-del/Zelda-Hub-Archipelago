@echo off
title Zelda Hub - Generateur de Release
cd /d "%~dp0"

echo ======================================================
echo          Zelda Hub - Generateur de Release
echo ======================================================
echo.

:: Verification de la presence de Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [Launcher] Lancement avec Python...
    python scripts\make_release.py
    goto end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    echo [Launcher] Lancement avec le lanceur py...
    py scripts\make_release.py
    goto end
)

echo [Erreur] Python n'a pas ete detecte sur votre systeme.
echo Veuillez installer Python (3.12 ou version superieure conseillee)
echo et vous assurer de cocher la case "Add Python to PATH" lors de l'installation.
echo.

:end
echo.
echo Appuyez sur une touche pour quitter...
pause >nul
