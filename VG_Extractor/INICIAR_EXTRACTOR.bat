@echo off
title Vinotinto Galactico - Extractor de Noticias
color 4F
echo ===================================================
echo   INICIANDO EXTRACTOR DE NOTICIAS (STREAMLIT)
echo ===================================================
echo.
echo Por favor espera unos segundos mientras carga el servidor...
echo Si es la primera vez, puede tardar un poco mas.
echo.
echo Para cerrar la aplicacion al terminar, simplemente cierra esta ventana negra.
echo.
cd /d "%~dp0"
python -m streamlit run app.py

echo.
echo [!] Ocurrio un error o la aplicacion se detuvo.
pause
