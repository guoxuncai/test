@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   Blog - first-time setup on this PC
echo   (git hooks / rebase / line endings / identity)
echo ==================================================
echo.

call "tools\find_python.bat"
if errorlevel 1 ( pause & exit /b 1 )

echo Interpreter: !PYEXE!
echo.

"!PYEXE!" "tools\setup_pc.py" %*
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
    echo [WARN] Script exited with code %RC%. See messages above.
)
echo --------------------------------------------------
echo Done. Use publish.bat to write, sync.bat to pull.
echo.
pause
endlocal
