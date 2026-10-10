@echo off
setlocal EnableExtensions
title Koruma - Kurulum
cd /d "%~dp0"

echo.
echo ============================================
echo   KORUMA - Kurulum Sihirbazi
echo   Kendi web sitenizin guvenlik tarayicisi
echo ============================================
echo.

call :main
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo Kurulum basariyla tamamlandi.
) else (
    echo Kurulum TAMAMLANAMADI. Yukaridaki hata mesajini okuyun.
)
echo.
echo Bu pencereyi kapatmak icin bir tusa basin...
pause >nul
exit /b %RC%


:main
set "ROOT=%~dp0"

echo [1/5] Python kontrol ediliyor...
set "PYCMD="
py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
if defined PYCMD goto :py_found
python -c "import sys" >nul 2>nul
if not errorlevel 1 set "PYCMD=python"
if defined PYCMD goto :py_found
python3 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PYCMD=python3"
if defined PYCMD goto :py_found
echo.
echo   HATA: Python bulunamadi.
echo   Lutfen https://www.python.org/downloads/ adresinden Python 3.9 veya uzerini kurun.
echo   Kurulum sirasinda "Add python.exe to PATH" kutusunu isaretlemeyi unutmayin.
echo   Not: Microsoft Store kisayolu gercek Python degildir, python.org surumunu kurun.
exit /b 1

:py_found
%PYCMD% -c "import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)" >nul 2>nul
if errorlevel 1 (
    echo   HATA: Python surumu cok eski. Python 3.9 veya uzeri gerekli.
    exit /b 1
)
for /f "tokens=2" %%v in ('%PYCMD% --version 2^>^&1') do set "PYVER=%%v"
echo   Bulundu: Python %PYVER% [%PYCMD%]

echo.
echo [2/5] Node.js kontrol ediliyor...
where node >nul 2>nul
if errorlevel 1 (
    echo   HATA: Node.js bulunamadi.
    echo   Lutfen https://nodejs.org adresinden Node.js 18 veya uzeri LTS surumunu kurun.
    exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
    echo   HATA: npm bulunamadi. Node.js kurulumunu yeniden yapin.
    exit /b 1
)
for /f "delims=" %%v in ('node --version') do set "NODEVER=%%v"
echo   Bulundu: Node.js %NODEVER%

echo.
echo [3/5] Python kutuphaneleri kuruluyor...
%PYCMD% -m pip --version >nul 2>nul
if errorlevel 1 (
    echo   HATA: pip bulunamadi. Python kurulumunu pip dahil olacak sekilde yenileyin.
    exit /b 1
)
%PYCMD% -m pip install --upgrade pip --quiet >nul 2>nul
%PYCMD% -m pip install -e . --quiet
if not errorlevel 1 goto :pip_ok
echo   Normal kurulum basarisiz oldu, --user ile tekrar deneniyor...
%PYCMD% -m pip install -e . --quiet --user
if not errorlevel 1 goto :pip_ok
echo.
echo   HATA: Python kutuphaneleri kurulamadi. Yukaridaki hata mesajini kontrol edin.
exit /b 1

:pip_ok
echo   Tamamlandi.

echo.
echo [4/5] Masaustu uygulamasi bagimliliklari kuruluyor - npm install
echo   Bu islem birkac dakika surebilir, lutfen bekleyin...
pushd "%ROOT%desktop"
call npm install --no-fund --no-audit --loglevel=error
if errorlevel 1 (
    popd
    echo   HATA: npm install basarisiz oldu.
    exit /b 1
)
echo   Tamamlandi.

echo.
echo [5/5] Masaustu arayuzu derleniyor...
call npm run build:ui --silent
if errorlevel 1 (
    popd
    echo   HATA: Arayuz derlenemedi.
    exit /b 1
)
popd
echo   Tamamlandi.

echo.
echo ============================================
echo   KURULUM TAMAMLANDI
echo ============================================
echo.
echo   Uygulamayi calistirmak icin: baslat.bat dosyasina cift tiklayin
echo   Komut satirindan           : koruma https://siteniz.com
echo   Windows kurulum paketi     : desktop klasorunde  npm run dist:win
echo.

set "LAUNCH=E"
set /p "LAUNCH=Simdi masaustu uygulamasini baslatmak ister misiniz? [E/h] "
if /i "%LAUNCH%"=="E" (
    pushd "%ROOT%desktop"
    start "Koruma" cmd /c "npm start"
    popd
)
exit /b 0
