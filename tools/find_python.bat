@echo off
rem ============================================================
rem  Shared helper: detect a usable Python interpreter.
rem  Result is returned in the PYEXE variable.
rem  Do not double-click this file directly.
rem
rem  NOTE: python.exe / py.exe under WindowsApps are Microsoft Store
rem        app-execution aliases. They cannot run scripts, so they
rem        must be skipped.
rem
rem  All paths are captured with "delims=" so install locations that
rem  contain spaces (e.g. C:\Program Files\Python38) stay intact.
rem  Parsing "py -0p" output is avoided on purpose: its last line has
rem  no trailing newline, which makes "for /f" drop it entirely.
rem ============================================================
set "PYEXE="

rem 1) py launcher: let Python itself report its absolute path.
for /f "delims=" %%p in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
    if not defined PYEXE if exist "%%p" set "PYEXE=%%p"
)

rem 2) Fall back to "where python", skipping the WindowsApps alias.
if not defined PYEXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        echo %%i | findstr /i "WindowsApps" >nul
        if errorlevel 1 if not defined PYEXE if exist "%%i" set "PYEXE=%%i"
    )
)

rem 3) Last resort: common install locations.
if not defined PYEXE (
    for %%d in (
        "%LocalAppData%\Programs\Python"
        "C:\Python312" "C:\Python311" "C:\Python310"
        "C:\Program Files\Python312" "C:\Program Files\Python311"
        "%ProgramFiles%\Python312" "%ProgramFiles%\Python311"
    ) do (
        if not defined PYEXE (
            for /f "delims=" %%p in ('dir /b /s "%%~d\python.exe" 2^>nul') do (
                if not defined PYEXE if exist "%%p" set "PYEXE=%%p"
            )
        )
    )
)

rem Final check: the resolved path must exist.
if defined PYEXE if not exist "%PYEXE%" set "PYEXE="

if not defined PYEXE (
    echo [ERROR] No usable Python interpreter found.
    echo.
    echo   If Python is installed, make sure "Add Python to PATH" was
    echo   checked during setup, then close this window and retry.
    echo   Download: https://www.python.org/downloads/
    echo.
    echo   You can also run it manually, for example:
    echo     "C:\Python312\python.exe" tools\publish.py
    echo.
    exit /b 1
)
exit /b 0
