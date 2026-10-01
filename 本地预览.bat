@echo off
chcp 65001 >nul
cd /d %~dp0

echo 正在更新文章索引并启动本地预览服务...
echo 浏览器打开 http://127.0.0.1:8000  按 Ctrl+C 结束
echo.

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY (
    echo [错误] 未检测到 Python
    pause
    exit /b 1
)

%PY% tools\publish.py --serve
pause
