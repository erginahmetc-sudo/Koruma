@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Koruma - Kurulum

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║        KORUMA - Kurulum Sihirbazi         ║
echo   ║   Kendi web sitenizin guvenlik tarayicisi ║
echo   ╚══════════════════════════════════════════╝
echo.

set ROOT=%~dp0
cd /d "%ROOT%"

REM --- Python kontrolu -------------------------------------------------
echo [1/5] Python kontrol ediliyor...
set PYCMD=
where py >nul 2>nul && set PYCMD=py
if not defined PYCMD (
    where python >nul 2>nul && set PYCMD=python
)
if not defined PYCMD (
    echo.
    echo   HATA: Python bulunamadi.
    echo   Lutfen https://www.python.org/downloads/ adresinden Python 3.9+ kurun.
    echo   Kurulum sirasinda "Add Python to PATH" kutusunu isaretlemeyi unutmayin.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('%PYCMD% --version 2^>^&1') do set PYVER=%%v
echo   Bulundu: Python %PYVER% (%PYCMD%)

REM --- Node.js kontrolu --------------------------------------------------
echo.
echo [2/5] Node.js kontrol ediliyor...
where node >nul 2>nul
if errorlevel 1 (
    echo.
    echo   HATA: Node.js bulunamadi.
    echo   Lutfen https://nodejs.org adresinden Node.js 18+ (LTS) kurun.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version') do set NODEVER=%%v
echo   Bulundu: Node.js %NODEVER%

REM --- Python bagimliliklari ----------------------------------------------
echo.
echo [3/5] Python kutuphaneleri kuruluyor (requests, beautifulsoup4, dnspython, reportlab)...
%PYCMD% -m pip install --upgrade pip --quiet >nul 2>nul
%PYCMD% -m pip install -e . --quiet
if errorlevel 1 (
    echo   Normal kurulum basarisiz oldu, --user ile tekrar deneniyor...
    %PYCMD% -m pip install -e . --quiet --user
    if errorlevel 1 (
        echo   HATA: Python kutuphaneleri kurulamadi. Yukaridaki hatayi kontrol edin.
        pause
        exit /b 1
    )
)
echo   Tamamlandi.

REM --- npm bagimliliklari -------------------------------------------------
echo.
echo [4/5] Masaustu uygulamasi bagimliliklari kuruluyor (npm install)...
echo   Bu islem birkac dakika surebilir, lutfen bekleyin...
pushd "%ROOT%desktop"
call npm install --no-fund --no-audit --loglevel=error
if errorlevel 1 (
    echo   HATA: npm install basarisiz oldu.
    popd
    pause
    exit /b 1
)
popd
echo   Tamamlandi.

REM --- Arayuzu derle -------------------------------------------------------
echo.
echo [5/5] Masaustu arayuzu derleniyor...
pushd "%ROOT%desktop"
call npm run build:ui --silent
popd
echo   Tamamlandi.

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║           KURULUM TAMAMLANDI!             ║
echo   ╚══════════════════════════════════════════╝
echo.
echo   Koruma'yi su sekilde calistirabilirsiniz:
echo.
echo     1) Masaustu uygulamasi : baslat.bat dosyasina cift tiklayin
echo        (veya desktop klasorunde "npm start")
echo.
echo     2) Komut satirindan     : koruma https://siteniz.com
echo.
echo     3) Windows .exe paketi  : desktop klasorunde "npm run dist:win"
echo        (kurulum dosyasi desktop\release\ klasorune yazilir)
echo.

set /p LAUNCH="Simdi masaustu uygulamasini baslatmak ister misiniz? [E/h] "
if /i "%LAUNCH%"=="" set LAUNCH=E
if /i "%LAUNCH%"=="E" (
    pushd "%ROOT%desktop"
    start "" npm start
    popd
)

echo.
pause
