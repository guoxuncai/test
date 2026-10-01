@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   Blog - scan posts / build index / push GitHub
echo ==================================================
echo.

set "PYEXE="

rem 1) prefer the py launcher, which reports real interpreter paths
rem    (the stub py.exe under WindowsApps cannot run scripts)
for /f "usebackq tokens=2*" %%a in (`py -0p 2^>nul`) do (
    if not defined PYEXE (
        echo %%b | findstr /i "python.exe" >nul
        if not errorlevel 1 set "PYEXE=%%b"
        if not defined PYEXE (
            echo %%a | findstr /i "python.exe" >nul
            if not errorlevel 1 set "PYEXE=%%a"
        )
    )
)

rem 2) fall back to where python, skipping the WindowsApps app alias
if not defined PYEXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        echo %%i | findstr /i "WindowsApps" >nul
        if errorlevel 1 if not defined PYEXE set "PYEXE=%%i"
    )
)

if not defined PYEXE (
    echo [ERROR] No usable Python interpreter found.
    echo.
    echo   If you just installed Python, make sure "Add Python to PATH"
    echo   was checked, then close this window and double-click again.
    echo   Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Interpreter: !PYEXE!
echo.

"!PYEXE!" "tools\publish.py" %*
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
    echo [WARN] Script exited with code %RC%. See messages above.
    echo.
)
echo --------------------------------------------------
echo Done. GitHub Pages refreshes in about 1-2 minutes.
echo Site: https://guoxuncai.github.io/test/
echo.
pause
endlocal
