# TTS Reader

Aplicación para la bandeja del sistema de Windows que lee en voz alta el texto seleccionado usando voces **Google Cloud TTS Neural2** — las mismas voces neurales de alta calidad que usa Google en Android.

> 🇬🇧 [English version below](#english)

---

## Características

- Vive en la bandeja del sistema (junto al reloj), siempre disponible
- Seleccioná cualquier texto en cualquier app → presioná el shortcut → lo lee en voz alta
- Usa voces **Neural2 de Google Cloud TTS** (naturales, alta calidad)
- **Control de velocidad sin distorsión** (0.5x – 4.0x) via ffmpeg atempo — inteligible incluso a velocidades altas
- Hotkey, voz, velocidad y tono configurables
- Configuración guardada entre sesiones
- Opción de arrancar con Windows
- Ejecutable `.exe` disponible (no requiere Python)

## Inicio rápido

### Opción A: EXE standalone (sin Python)

Descargá `TTS Reader.exe` desde [Releases](../../releases) y ejecutalo directamente.

### Opción B: Desde el código fuente

```bash
pip install -r requirements.txt
python tts_tray.py
```

O hacé doble clic en `TTS Reader.pyw` para abrir sin ventana de consola.

## Configuración: API Key de Google Cloud TTS

Necesitás una API key gratuita de Google Cloud para usar la app.

1. Entrá a [console.cloud.google.com](https://console.cloud.google.com)
2. Creá un proyecto (o seleccioná uno existente)
3. Activá la **Cloud Text-to-Speech API**: [link directo](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
4. Andá a **APIs & Services → Credentials → Create Credentials → API Key**
5. Copiá la key
6. Abrí la app → clic derecho en el ícono de la bandeja → **Configuración** → pegá la key → Guardar

La app incluye un tutorial integrado (clic derecho → Tutorial) con links clickeables para cada paso.

> **Capa gratuita**: Google Cloud TTS da 1 millón de caracteres por mes gratis para voces WaveNet/Neural2.

## Uso

1. Seleccioná texto en cualquier aplicación
2. Presioná `Ctrl+Alt+R` (shortcut por defecto)
3. El texto se lee en voz alta con la voz configurada

Para detener la reproducción, presioná el shortcut de nuevo o clic derecho en el ícono → **Detener**.

## Configuración disponible

Clic derecho en el ícono → **Configuración**:

| Ajuste | Descripción |
|--------|-------------|
| API Key | Tu clave de Google Cloud TTS |
| Hotkey | Shortcut de teclado para activar la lectura |
| Voz | Selección de voz Neural2 (Español/Inglés disponibles) |
| Velocidad | Velocidad de reproducción 0.5x – 4.0x |
| Tono | Ajuste del tono de la voz |

## Voces disponibles

| Voz | Idioma | Género |
|-----|--------|--------|
| es-US-Neural2-A | Español (EE.UU.) | Femenino |
| es-US-Neural2-B | Español (EE.UU.) | Masculino |
| es-ES-Neural2-A | Español (España) | Femenino |
| es-ES-Neural2-C | Español (España) | Masculino |
| en-US-Neural2-A | Inglés (EE.UU.) | Femenino |
| en-US-Neural2-D | Inglés (EE.UU.) | Masculino |

## Compilar el EXE desde el código fuente

Requiere PyInstaller:

```bash
pip install pyinstaller
build_exe.bat
```

El resultado `dist/TTS Reader.exe` es un ejecutable standalone (~72 MB, incluye ffmpeg).

## Requisitos

- Windows 10/11
- Python 3.10+ (solo si corrés desde el código fuente)
- Conexión a internet (para las llamadas a la API)
- API key de Google Cloud

## Dependencias

```
pystray       # Ícono en la bandeja del sistema
keyboard      # Hotkeys globales
pyperclip     # Acceso al portapapeles
requests      # Llamadas HTTP a la API de Google
pygame-ce     # Reproducción de audio
Pillow        # Renderizado del ícono
imageio-ffmpeg # ffmpeg incluido para control de velocidad
```

## Licencia

MIT

---

## English

<a name="english"></a>

Windows system tray app that reads selected text aloud using **Google Cloud TTS Neural2** voices — the same high-quality neural voices used by Google on Android.

### Features

- Lives in the system tray (near the clock), always ready
- Select any text in any app → press shortcut → it reads it aloud
- Uses Google Cloud TTS **Neural2** voices (natural, high-quality)
- **Pitch-preserving speed control** (0.5x – 4.0x) via ffmpeg atempo — intelligible even at high speeds
- Configurable hotkey, voice, speed, and pitch
- Settings saved between sessions
- Optional startup with Windows
- Standalone `.exe` available (no Python required)

### Quick Start

**Option A: Standalone EXE (no Python needed)**

Download `TTS Reader.exe` from [Releases](../../releases) and run it.

**Option B: Run from source**

```bash
pip install -r requirements.txt
python tts_tray.py
```

Or double-click `TTS Reader.pyw` to launch without a console window.

### Setup: Google Cloud TTS API Key

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project (or select an existing one)
3. Enable the **Cloud Text-to-Speech API**: [direct link](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
4. Go to **APIs & Services → Credentials → Create Credentials → API Key**
5. Copy the key
6. Open the app → right-click tray icon → **Settings** → paste the key → Save

> **Free tier**: Google Cloud TTS gives 1 million characters/month free for WaveNet/Neural2 voices.

### Usage

1. Select text in any application
2. Press `Ctrl+Alt+R` (default shortcut)
3. The text is read aloud in the configured voice

### Requirements

- Windows 10/11
- Python 3.10+ (if running from source)
- Internet connection (for API calls)
- Google Cloud API key

### License

MIT
