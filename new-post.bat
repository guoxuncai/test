@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==================================================
echo   Blog - new post from template
echo ==================================================
echo.
echo   Category : finance / semiconductor
echo   Filename : e.g. 2026-10-02-market-review
echo.

call "tools\find_python.bat"
if errorlevel 1 ( pause & exit /b 1 )

set "CAT=%~1"
set "NAME=%~2"

if not defined CAT set "CAT=finance"
if "%~1"=="" set /p CAT=Category [default finance]:
if "%CAT%"=="" set "CAT=finance"

if "%~2"=="" set /p NAME=Filename without extension:
if "%NAME%"=="" (
    echo No filename given. Cancelled.
    pause
    exit /b 0
)

"!PYEXE!" "tools\publish.py" --draft %CAT% %NAME%

echo.
echo Tip: edit the file in your browser/editor, then double-click publish.bat to publish.
echo.
pause
endlocal
