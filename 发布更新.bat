@echo off
chcp 65001 >nul
cd /d %~dp0

echo ==================================================
echo   静态博客 - 扫描文章 / 更新索引 / 推送 GitHub
echo ==================================================
echo.

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY (
    echo [错误] 未检测到 Python，请先安装并加入环境变量 PATH
    echo        https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

%PY% tools\publish.py %*

echo.
echo --------------------------------------------------
echo 完成。GitHub Pages 通常在推送后 1-2 分钟自动更新。
echo.
pause
