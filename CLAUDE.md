# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Entorno Python

- Python 3.14+ requerido (`C:\Users\Héctor\AppData\Local\Python\pythoncore-3.14-64`)
- Usar siempre `python -m pip` (no `pip` directamente)
- **pygame no tiene wheel para Python 3.14** → usar `pygame-ce` (drop-in replacement, misma API)

## Comandos útiles

```bash
# Instalar dependencias
python -m pip install -r requirements.txt

# Ejecutar (con consola, para debug)
python tts_tray.py

# Ejecutar sin consola (modo normal de uso)
# Doble click en "TTS Reader.pyw", o:
pythonw.exe tts_tray.py

# Compilar a .exe standalone
build_exe.bat
# Output: dist/TTS Reader.exe (~72 MB, incluye ffmpeg)
```

## Arquitectura

Todo el código vive en un único archivo: `tts_tray.py`.

### Modelo de hilos
- **Hilo principal:** tkinter event loop (`TrayApp.run()` → `root.mainloop()`)
- **Hilo background:** `pystray.Icon.run()` (ícono del tray y menú)
- **Hilos bajo demanda:** síntesis TTS + reproducción (uno por lectura), preview en Settings

**Regla importante:** nunca llamar a tkinter desde un hilo que no sea el principal. Siempre usar `root.after(0, fn)` para despachar al hilo principal desde callbacks de pystray o keyboard.

### Clases principales

| Clase | Responsabilidad |
|-------|----------------|
| `Config` | Carga/guarda `tts_config.json`, acceso por atributos |
| `GoogleTTS` | Llama a la REST API de Google Cloud TTS, devuelve bytes MP3 |
| `AudioPlayer` | Maneja pygame mixer, aplica atempo via ffmpeg, thread-safe con Lock |
| `FloatingPlayer` | Ventana flotante siempre-visible con play/pausa durante lectura |
| `TrayApp` | Controlador principal: ícono, hotkey, orquesta todo |
| `SettingsWindow` | Diálogo modal de configuración (API key, voz, velocidad, tema) |
| `TutorialWindow` | Tutorial de 5 pasos para obtener API key de Google Cloud |

### Flujo de lectura (hotkey)
1. `_hotkey_cb()` → suelta modificadores, espera → `keyboard.send("ctrl+c")`
2. Compara con marcador UUID para detectar si había texto seleccionado
3. Llama a `GoogleTTS.synthesize()` siempre con `speakingRate=1.0`
4. `AudioPlayer.play(mp3, speed)` aplica `ffmpeg atempo` para la velocidad real
5. `FloatingPlayer` aparece con control de pausa

### Control de velocidad (WSOLA)
La API de TTS siempre recibe `speakingRate=1.0`. La velocidad se aplica post-síntesis con el filtro `atempo` de ffmpeg, que preserva el tono. Para velocidades fuera del rango 0.5–2.0 se encadenan filtros: ej. 3.0x = `atempo=2.0,atempo=1.5`. El binario de ffmpeg viene incluido via `imageio-ffmpeg`.

### Sistema de temas
`DARK_COLORS` y `LIGHT_COLORS` son dicts globales. `COLORS` apunta a uno de los dos según `config.theme`. `setup_theme(root)` configura `ttk.Style`. Al guardar Settings, se reasigna `COLORS` y se llama `setup_theme()` de nuevo. Los nuevos widgets creados después del cambio ya usan el nuevo tema.

### Configuración persistente
`tts_config.json` se guarda junto al script (o junto al `.exe` si está compilado). La clase `Config` detecta si corre como PyInstaller frozen (`sys.frozen`) y usa `sys.executable` para encontrar la ruta correcta.

### Startup con Windows
`_set_startup(enabled)` escribe en `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. Cuando corre como script usa `pythonw.exe` para evitar la consola.

## Detalles de la API de Google Cloud TTS

- Endpoint: `POST https://texttospeech.googleapis.com/v1/text:synthesize?key={API_KEY}`
- Límite: 4500 chars por request (`MAX_CHARS` en el código)
- Voces disponibles: 10 Neural2 en español (US/ES) e inglés (US/GB)
- Error 403 "has not been used": se detecta con regex, se muestra link clickable para habilitar la API

## Distribución

El `.exe` compilado incluye ffmpeg (via `imageio-ffmpeg`) y no requiere Python instalado. El archivo `tts_config.json` con la API key personal está en `.gitignore` y nunca se commitea.
