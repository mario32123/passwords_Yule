@echo off
title GestorPass - Servidor
cd /d "%~dp0"
echo.
echo  ============================================
echo    GestorPass - Iniciando servidor...
echo  ============================================
echo.
echo  Abre tu navegador en: http://localhost:5000
echo  Para detener el servidor presiona Ctrl+C
echo.
python run.py
pause
