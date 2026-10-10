@echo off
setlocal EnableExtensions
title Koruma
cd /d "%~dp0desktop"

if not exist node_modules (
    echo Once setup.bat dosyasini calistirmaniz gerekiyor.
    echo.
    pause
    exit /b 1
)

echo Koruma baslatiliyor... Uygulama calisirken bu pencereyi kapatmayin.
call npm start
if errorlevel 1 (
    echo.
    echo Uygulama baslatilamadi. Yukaridaki hata mesajini okuyun.
    pause
    exit /b 1
)
