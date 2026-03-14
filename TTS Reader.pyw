"""
Launcher sin consola para TTS Reader.
Doble clic en este archivo para abrir el programa sin ventana de terminal.
"""
import os
import sys
import subprocess

_here = os.path.dirname(os.path.abspath(__file__))
_script = os.path.join(_here, "tts_tray.py")
_pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")

if not os.path.exists(_pythonw):
    _pythonw = sys.executable

subprocess.Popen([_pythonw, _script])
