# TTS Reader

Windows system tray app that reads selected text aloud using **Google Cloud TTS Neural2** voices — the same high-quality neural voices used by Google on Android.

## Features

- Lives in the system tray (near the clock), always ready
- Select any text in any app → press shortcut → it reads it aloud
- Uses Google Cloud TTS **Neural2** voices (natural, high-quality)
- **Pitch-preserving speed control** (0.5x – 4.0x) via ffmpeg atempo — intelligible even at high speeds
- Configurable hotkey, voice, speed, and pitch
- Settings saved between sessions
- Optional startup with Windows
- Standalone `.exe` available (no Python required)

## Quick Start

### Option A: Standalone EXE (no Python needed)

Download `TTS Reader.exe` from [Releases](../../releases) and run it.

### Option B: Run from source

```bash
pip install -r requirements.txt
python tts_tray.py
```

Or double-click `TTS Reader.pyw` to launch without a console window.

## Setup: Google Cloud TTS API Key

You need a free Google Cloud API key to use the app.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project (or select an existing one)
3. Enable the **Cloud Text-to-Speech API**: [direct link](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
4. Go to **APIs & Services → Credentials → Create Credentials → API Key**
5. Copy the key
6. Open the app → right-click tray icon → **Settings** → paste the key → Save

The app includes a built-in tutorial (right-click → Tutorial) with clickable links for each step.

> **Free tier**: Google Cloud TTS gives 1 million characters/month free for WaveNet/Neural2 voices.

## Usage

1. Select text in any application
2. Press `Ctrl+Alt+R` (default shortcut)
3. The text is read aloud in the configured voice

To stop playback at any time, press the shortcut again or right-click the tray icon → **Stop**.

## Configuration

Right-click the tray icon → **Settings**:

| Setting | Description |
|---------|-------------|
| API Key | Your Google Cloud TTS API key |
| Hotkey | Keyboard shortcut to trigger reading |
| Voice | Neural2 voice selection (Spanish/English included) |
| Speed | Playback speed 0.5x – 4.0x |
| Pitch | Voice pitch adjustment |

## Available Voices

| Voice | Language | Gender |
|-------|----------|--------|
| es-US-Neural2-A | Spanish (US) | Female |
| es-US-Neural2-B | Spanish (US) | Male |
| es-ES-Neural2-A | Spanish (Spain) | Female |
| es-ES-Neural2-C | Spanish (Spain) | Male |
| en-US-Neural2-A | English (US) | Female |
| en-US-Neural2-D | English (US) | Male |

## Build EXE from source

Requires PyInstaller:

```bash
pip install pyinstaller
build_exe.bat
```

The resulting `dist/TTS Reader.exe` is a standalone executable (~72 MB, includes ffmpeg).

## Requirements

- Windows 10/11
- Python 3.10+ (if running from source)
- Internet connection (for API calls)
- Google Cloud API key

## Dependencies

```
pystray       # System tray icon
keyboard      # Global hotkeys
pyperclip     # Clipboard access
requests      # HTTP calls to Google API
pygame-ce     # Audio playback
Pillow        # Tray icon rendering
imageio-ffmpeg # Bundled ffmpeg for speed control
```

## License

MIT
