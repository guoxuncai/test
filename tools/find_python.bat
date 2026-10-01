@echo off
rem ============================================================
rem  Shared helper: detect a usable Python interpreter.
rem  Result is returned in the PYEXE variable.
rem  Do not double-click this file directly.
rem
rem  NOTE: python.exe / py.exe under WindowsApps are Microsoft Store
rem        app-execution aliases. They cannot run scripts, so they
rem        must be skipped.
rem ============================================================
set "PYEXE="

rem 1) Use the py launcher if present; "py -0p" lists real interpreter paths.
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

rem 2) Fall back to "where python", skipping the WindowsApps alias.
if not defined PYEXE (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        echo %%i | findstr /i "WindowsApps" >nul
        if errorlevel 1 if not defined PYEXE set "PYEXE=%%i"
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
                if not defined PYEXE set "PYEXE=%%p"
            )
        )
    )
)

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
