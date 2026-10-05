@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   Blog - sync only (pull --rebase from GitHub)
echo ==================================================
echo.

call "tools\find_python.bat"
if errorlevel 1 ( pause & exit /b 1 )

echo Interpreter: !PYEXE!
echo.

"!PYEXE!" "tools\publish.py" --sync-only
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
    echo [WARN] Script exited with code %RC%. See messages above.
    echo   If conflicts remain, resolve them manually:
    echo     git status
    echo     git pull --rebase
    echo.
)
echo --------------------------------------------------
echo Done. Working copy is up to date with GitHub.
echo.
pause
endlocal
