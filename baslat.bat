@echo off
chcp 65001 >nul
title Koruma
cd /d "%~dp0desktop"
if not exist node_modules (
    echo Once setup.bat dosyasini calistirmaniz gerekiyor.
    pause
    exit /b 1
)
start "" npm start
