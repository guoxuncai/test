@echo off
chcp 65001
echo ======================
echo 开始提交静态HTML文件
echo ======================
git add .
git commit -m "auto update: 本地html更新 %date% %time%"
git push origin main
echo 推送完成！
pause
