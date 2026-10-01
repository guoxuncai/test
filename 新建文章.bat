@echo off
chcp 65001 >nul
cd /d %~dp0

echo ==================================================
echo   新建一篇文章（从模板生成）
echo ==================================================
echo.
echo   分类可选： finance（财经简报） / semiconductor（半导体）
echo   文件名示例： 2026-10-01-节后首日市场观察
echo.

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
if not defined PY (
    echo [错误] 未检测到 Python
    pause
    exit /b 1
)

set /p CAT=请输入分类 (默认 finance):
if not defined CAT set CAT=finance

set /p NAME=请输入文件名(不含扩展名):
if not defined NAME (
    echo 未输入文件名，已取消。
    pause
    exit /b 0
)

%PY% tools\publish.py --draft %CAT% %NAME%

echo.
echo 提示：用浏览器打开编辑该文件，写完后双击「发布更新.bat」即可上线。
echo.
pause
