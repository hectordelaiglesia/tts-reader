@echo off
echo Construyendo TTS Reader.exe...
echo.

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "TTS Reader" ^
    --add-binary "%LOCALAPPDATA%\Python\pythoncore-3.14-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe;imageio_ffmpeg/binaries" ^
    --hidden-import pystray._win32 ^
    --hidden-import PIL._tkinter_finder ^
    tts_tray.py

echo.
if exist "dist\TTS Reader.exe" (
    echo Listo. El archivo esta en: dist\TTS Reader.exe
    echo Copialo donde quieras y ejecutalo directamente.
) else (
    echo ERROR: No se genero el ejecutable. Revisa los mensajes de arriba.
)
pause
