@echo off
REM Ghost CFO Agent — build script
REM Run this from the agent\ directory on a Windows machine with Python installed.
REM
REM Prerequisites (run once):
REM   pip install -r requirements.txt
REM
REM Output: dist\GhostCFOAgent.exe

setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo  Ghost CFO Agent — Build
echo ============================================================
echo.

REM Step 1: Generate icon
echo [1/3] Generating icon...
python assets\generate_icon.py
if errorlevel 1 (
    echo [ERROR] Icon generation failed.
    pause
    exit /b 1
)
echo       Done: assets\ghostcfo.ico

REM Step 2: Clean previous build
echo [2/3] Cleaning previous build...
if exist dist\GhostCFOAgent.exe del /f /q dist\GhostCFOAgent.exe
if exist build rmdir /s /q build

REM Step 3: PyInstaller
echo [3/3] Running PyInstaller...
pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed. Check output above.
    pause
    exit /b 1
)
echo       Done: dist\GhostCFOAgent.exe

REM Step 4: Copy exe to installer\Output so Inno Setup picks it up
echo [4/4] Copying to installer\Output...
if not exist installer\Output mkdir installer\Output
copy /y dist\GhostCFOAgent.exe installer\Output\GhostCFOAgent.exe >nul

REM Step 5: Inno Setup
set ISCC="%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if exist %ISCC% (
    echo [5/5] Building installer...
    %ISCC% installer\ghostcfo_agent.iss
    if errorlevel 1 (
        echo [ERROR] Inno Setup compile failed.
        pause
        exit /b 1
    )
) else (
    echo [SKIP] Inno Setup not found - skipping installer build.
    echo        Install from: https://jrsoftware.org/isdl.php
)

echo.
echo ============================================================
echo  Build complete!
echo  Exe:       dist\GhostCFOAgent.exe
echo  Installer: installer\Output\GhostCFOAgentSetup.exe
echo.
echo  Install on client server:
echo    GhostCFOAgent.exe install ^
echo      --api-key=^<key from Ghost CFO admin^> ^
echo      --server=SERVERNAME\SQLEXPRESS ^
echo      --db=PASTEL_EVOLUTION_DB ^
echo      --username=ghostcfo_reader ^
echo      --password=^<sql password^> ^
echo      --encryption-key=^<AES key from Ghost CFO admin^>
echo ============================================================
echo.
pause
