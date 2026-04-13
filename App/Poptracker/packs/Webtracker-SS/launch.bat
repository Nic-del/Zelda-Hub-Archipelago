@echo off
setlocal EnableDelayedExpansion

set "IP=%~1"
set "PORT=%~2"
set "SLOT=%~3"
set "MDP=%~4"

if "%IP%"=="" (
    echo Usage: launch.bat IP PORT SLOT [MDP]
    echo Example: launch.bat archipelago.gg 38281 MySlot MyPassword
    pause
    exit /b
)

if "%PORT%"=="" (
    echo Error: Port is required.
    pause
    exit /b
)

if "%SLOT%"=="" (
    echo Error: Slot name is required.
    pause
    exit /b
)

set "URL=http://localhost:5173/#/?ip=!IP!&port=!PORT!&slot=!SLOT!&autolaunch=true&layout=grid"
if not "!MDP!"=="" (
    set "URL=!URL!&mdp=!MDP!"
)

echo Opening tracker at:
echo !URL!
start "" "!URL!"
