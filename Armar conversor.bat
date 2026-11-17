@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Armando el Conversor de minifaces

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY goto sinpython
if not exist "base_fm.json.gz" goto sinbase

echo === 1/3  Instalando PyInstaller ===
%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 goto error

echo.
echo === 2/3  Armando "Conversor de minifaces.exe" (con la lista del FM adentro) ===
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name "Conversor de minifaces" --icon icono.ico --add-data "icono.ico;." --add-data "base_fm.json.gz;." --exclude-module playwright --exclude-module PIL conversor_minifaces.py
if errorlevel 1 goto error

echo.
echo === 3/3  Limpiando ===
copy /y "dist\Conversor de minifaces.exe" "Conversor de minifaces.exe" >nul
rmdir /s /q build
rmdir /s /q dist
del /q "Conversor de minifaces.spec"

echo.
echo LISTO: "Conversor de minifaces.exe" esta en esta carpeta.
echo Eso es lo que le pasas a la gente, junto con los packs de "Packs para compartir".
echo.
pause
exit /b

:sinbase
echo Falta "base_fm.json.gz" (la lista del FM que va adentro del conversor).
echo Abri el bot, pestana "Base FM - PES", Paso 1, boton A, y elegi tu players.csv.
echo Cuando termine, volve a abrir este archivo.
pause
exit /b

:error
echo.
echo Algo fallo armando el .exe. Mandale una captura de esta ventana a Claude.
pause
exit /b

:sinpython
echo No encontre Python en esta PC. Instalalo de https://www.python.org/downloads/
echo tildando "Add python.exe to PATH" y volve a abrir este archivo.
pause
