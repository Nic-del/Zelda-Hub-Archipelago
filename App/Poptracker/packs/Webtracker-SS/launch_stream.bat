@echo off
setlocal EnableDelayedExpansion

set "PART=%~1"
set "IP=%~2"
set "PORT=%~3"
set "SLOT=%~4"
set "MDP=%~5"

if "%PART%"=="" (
    echo Usage: launch_stream.bat PART IP PORT SLOT [MDP]
    echo Example: launch_stream.bat items archipelago.gg 38281 MySlot MyPassword
    echo Available parts: items, map, locations, chat, dungeons, counters
    pause
    exit /b
)

if "%IP%"=="" (
    echo Error: IP is required.
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

REM Structure for HashRouter: /#/path?query
set "URL=http://localhost:5173/#/!PART!?ip=!IP!&port=!PORT!&slot=!SLOT!&autolaunch=true&layout=grid"
if not "!MDP!"=="" (
    set "URL=!URL!&mdp=!MDP!"
)

echo Opening stream view for [!PART!] at:
echo !URL!
start "" "!URL!"
