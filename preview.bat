@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   Blog - local preview server
echo ==================================================
echo.

call "tools\find_python.bat"
if errorlevel 1 ( pause & exit /b 1 )

echo Interpreter: !PYEXE!
echo Starting local preview at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.

"!PYEXE!" "tools\publish.py" --serve
pause
endlocal
