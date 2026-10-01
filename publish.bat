@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   Blog - scan posts / build index / push GitHub
echo ==================================================
echo.

call "tools\find_python.bat"
if errorlevel 1 ( pause & exit /b 1 )

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
