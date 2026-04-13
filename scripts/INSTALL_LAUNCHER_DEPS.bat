@echo off
setlocal enabledelayedexpansion

echo ===========================================
echo INSTALLATION DES DEPENDANCES DU LAUNCHER
echo ===========================================
echo.

:: Vérification de la présence du dossier python_src
if not exist "..\python_src" (
    echo [ERREUR] Le dossier 'python_src' est introuvable.
    echo Assurez-vous de lancer ce script depuis la racine du projet.
    pause
    exit /b
)

:: Vérification de la présence de requirements.txt
if not exist "..\python_src\requirements.txt" (
    echo [ERREUR] Le fichier 'python_src\requirements.txt' est introuvable.
    pause
    exit /b
)

echo ETAPE 1 : Verification de Python...

:: On essaye de trouver python ou py
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set PY_CMD=python
    ) else (
        echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
        echo Veuillez l'installer depuis https://www.python.org/
        pause
        exit /b
    )
)

echo Utilisation de la commande : !PY_CMD!
!PY_CMD! --version

echo.
echo ETAPE 2 : Mise a jour de pip...
!PY_CMD! -m pip install --upgrade pip

echo.
echo ETAPE 3 : Installation des dependances (requirements.txt)...
!PY_CMD! -m pip install -r ..\python_src\requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] L'installation a echoue. 
    echo Verifiez votre connexion internet ou essayez en tant qu'administrateur.
) else (
    echo.
    echo [SUCCES] Toutes les dependances sont installees !
)

echo.
echo ===========================================
pause
