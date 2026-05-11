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

echo.
echo ============================================================
echo  Build complete!
echo  Output: dist\GhostCFOAgent.exe
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
