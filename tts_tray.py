#!/usr/bin/env python3
"""
TTS Tray - Lee texto seleccionado con Google Cloud Text-to-Speech (voces Neural2).

Uso:
  1. Correr: python tts_tray.py
  2. Aparece ícono en bandeja del sistema
  3. Click derecho → Configuración → ingresar API key
  4. Seleccionar texto en cualquier ventana → presionar Ctrl+Alt+R
"""

import os
import sys
import json
import time
import base64
import threading
import tempfile
import uuid
import shutil
import subprocess
import webbrowser
import winreg
import tkinter as tk
from tkinter import ttk, messagebox

import pystray
from PIL import Image, ImageDraw
import keyboard
import pyperclip
import requests
import pygame

# ──────────────────────────────────────────────────────────────
# VOCES DISPONIBLES
# ──────────────────────────────────────────────────────────────

VOICES = [
    ("es-US-Neural2-A", "es-US", "Español (EEUU) — Femenina"),
    ("es-US-Neural2-B", "es-US", "Español (EEUU) — Masculina"),
    ("es-US-Neural2-C", "es-US", "Español (EEUU) — Femenina 2"),
    ("es-ES-Neural2-A", "es-ES", "Español (España) — Femenina"),
    ("es-ES-Neural2-B", "es-ES", "Español (España) — Masculina"),
    ("es-ES-Neural2-C", "es-ES", "Español (España) — Femenina 2"),
    ("en-US-Neural2-A", "en-US", "English (US) — Female"),
    ("en-US-Neural2-D", "en-US", "English (US) — Male"),
    ("en-GB-Neural2-A", "en-GB", "English (UK) — Female"),
    ("en-GB-Neural2-B", "en-GB", "English (UK) — Male"),
]

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────

# Cuando se compila con PyInstaller, __file__ apunta a una carpeta temporal
# interna. Usar sys.executable para guardar la config junto al .exe.
if getattr(sys, "frozen", False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "tts_config.json")

DEFAULT_CONFIG = {
    "api_key": "",
    "hotkey": "ctrl+alt+r",
    "voice_name": "es-US-Neural2-A",
    "speaking_rate": 1.0,
    "pitch": 0.0,
}


class Config:
    def __init__(self):
        self._d = dict(DEFAULT_CONFIG)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    self._d.update(json.load(f))
            except Exception:
                pass

    def save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._d, f, indent=2, ensure_ascii=False)

    def __getattr__(self, k):
        if k.startswith("_"):
            raise AttributeError(k)
        return self._d.get(k)

    def __setattr__(self, k, v):
        if k.startswith("_"):
            super().__setattr__(k, v)
        else:
            self._d[k] = v

    def lang_for(self, voice_name):
        for name, lang, _ in VOICES:
            if name == voice_name:
                return lang
        return "es-US"


# ──────────────────────────────────────────────────────────────
# GOOGLE CLOUD TTS
# ──────────────────────────────────────────────────────────────

TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
MAX_CHARS = 4500  # Google limit is ~5000 bytes


class APINotEnabledError(Exception):
    """La API de TTS no está habilitada en el proyecto de Google Cloud."""
    def __init__(self, enable_url: str):
        super().__init__("API no habilitada")
        self.enable_url = enable_url


def _show_api_not_enabled(parent, enable_url: str):
    """Diálogo con link clickeable para habilitar la API."""
    dlg = tk.Toplevel(parent)
    dlg.title("API no habilitada")
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.focus_force()

    f = ttk.Frame(dlg, padding=20)
    f.pack(fill="both", expand=True)

    ttk.Label(f, text="⚠  La API de Text-to-Speech no está habilitada",
              font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

    ttk.Label(
        f,
        text="Tenés la API Key correcta, pero falta activar la API\n"
             "de Text-to-Speech en tu proyecto de Google Cloud.\n\n"
             "Es un solo clic: hacé clic en el link de abajo,\n"
             "luego presioná el botón azul \"Habilitar\".\n"
             "Puede tardar 1-2 minutos en activarse.",
        justify="left",
        font=("Segoe UI", 9),
    ).pack(anchor="w", pady=(0, 12))

    lnk = tk.Label(
        f,
        text="→ Habilitar la API de Text-to-Speech (clic aquí)",
        foreground="#1a73e8",
        font=("Segoe UI", 9, "underline"),
        cursor="hand2",
    )
    lnk.pack(anchor="w", pady=(0, 16))
    lnk.bind("<Button-1>", lambda _: webbrowser.open(enable_url))

    ttk.Button(f, text="Cerrar", command=dlg.destroy).pack(anchor="e")

    dlg.update_idletasks()
    w, h = dlg.winfo_width(), dlg.winfo_height()
    sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
    dlg.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


class GoogleTTS:
    def __init__(self, config: Config):
        self.config = config

    def synthesize(self, text: str) -> bytes:
        if not self.config.api_key:
            raise ValueError("API key no configurada. Abrí Configuración.")
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
        body = {
            "input": {"text": text},
            "voice": {
                "languageCode": self.config.lang_for(self.config.voice_name),
                "name": self.config.voice_name,
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0,  # Velocidad siempre 1.0 — se aplica con atempo
                "pitch": self.config.pitch,
            },
        }
        r = requests.post(
            TTS_URL,
            params={"key": self.config.api_key},
            json=body,
            timeout=15,
        )
        if r.status_code != 200:
            try:
                err_body = r.json().get("error", {})
                err_msg = err_body.get("message", r.text)
            except Exception:
                err_msg = r.text
            # Error 403: API no habilitada en el proyecto
            if r.status_code == 403 and "has not been used" in err_msg:
                import re
                match = re.search(r"https://console\.developers\.google\.com\S+", err_msg)
                enable_url = match.group(0).rstrip(".") if match else \
                    "https://console.cloud.google.com/apis/library/texttospeech.googleapis.com"
                raise APINotEnabledError(enable_url)
            raise RuntimeError(f"Error {r.status_code}: {err_msg}")
        return base64.b64decode(r.json()["audioContent"])


# ──────────────────────────────────────────────────────────────
# FFMPEG / ATEMPO (time-stretching para velocidades altas)
# ──────────────────────────────────────────────────────────────

def _find_ffmpeg() -> str | None:
    """Devuelve la ruta a ffmpeg: primero el del sistema, luego imageio-ffmpeg."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _atempo_filter(speed: float) -> str:
    """Construye el filtro atempo encadenado para cualquier velocidad.
    atempo solo acepta valores entre 0.5 y 2.0, hay que encadenar para el resto."""
    parts = []
    s = speed
    while s > 2.0:
        parts.append("atempo=2.0")
        s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    if abs(s - 1.0) > 0.001:
        parts.append(f"atempo={s:.6f}")
    return ",".join(parts) if parts else "atempo=1.0"


_FFMPEG = _find_ffmpeg()


# ──────────────────────────────────────────────────────────────
# REPRODUCTOR DE AUDIO
# ──────────────────────────────────────────────────────────────

class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self._tmp_in  = None
        self._tmp_out = None
        self._lock = threading.Lock()

    def play(self, mp3: bytes, speed: float = 1.0):
        with self._lock:
            pygame.mixer.music.stop()

            old_in  = self._tmp_in
            old_out = self._tmp_out

            # Guardar MP3 en archivo temporal de entrada
            fd, in_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            with open(in_path, "wb") as f:
                f.write(mp3)
            self._tmp_in  = in_path
            self._tmp_out = None

            play_path = in_path

            # Aplicar time-stretching con atempo si la velocidad != 1.0
            if abs(speed - 1.0) > 0.05 and _FFMPEG:
                fd2, out_path = tempfile.mkstemp(suffix=".mp3")
                os.close(fd2)
                try:
                    result = subprocess.run(
                        [_FFMPEG, "-y", "-i", in_path,
                         "-filter:a", _atempo_filter(speed),
                         "-q:a", "2", out_path],
                        capture_output=True,
                        timeout=15,
                    )
                    if result.returncode == 0:
                        play_path = out_path
                        self._tmp_out = out_path
                    else:
                        try: os.unlink(out_path)
                        except Exception: pass
                except Exception:
                    try: os.unlink(out_path)
                    except Exception: pass

            pygame.mixer.music.load(play_path)
            pygame.mixer.music.play()

            # Limpiar archivos temporales anteriores
            for old in (old_in, old_out):
                if old:
                    try: os.unlink(old)
                    except Exception: pass

    def stop(self):
        pygame.mixer.music.stop()


# ──────────────────────────────────────────────────────────────
# ÍCONO DEL TRAY
# ──────────────────────────────────────────────────────────────

def _make_icon() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Fondo azul Google
    d.ellipse([1, 1, size - 1, size - 1], fill=(66, 133, 244, 255))
    # Altavoz blanco
    d.polygon([(14, 20), (26, 20), (38, 12), (38, 52), (26, 44), (14, 44)], fill="white")
    # Ondas de sonido
    d.arc([40, 20, 58, 44], -70, 70, fill="white", width=3)
    d.arc([44, 25, 58, 39], -70, 70, fill="white", width=3)
    return img


# ──────────────────────────────────────────────────────────────
# APP PRINCIPAL
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# INICIO CON WINDOWS
# ──────────────────────────────────────────────────────────────

_STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_STARTUP_APP_NAME = "TTSReader"


def _startup_exe_cmd() -> str:
    """Devuelve el comando para el registro de inicio con Windows."""
    if getattr(sys, "frozen", False):
        # Compilado como .exe
        return f'"{sys.executable}"'
    else:
        # Usar pythonw.exe para no mostrar consola al arrancar con Windows
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        return f'"{pythonw}" "{os.path.abspath(__file__)}"'


def _is_startup_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY)
        winreg.QueryValueEx(key, _STARTUP_APP_NAME)
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def _set_startup(enabled: bool):
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE
    )
    if enabled:
        winreg.SetValueEx(key, _STARTUP_APP_NAME, 0, winreg.REG_SZ, _startup_exe_cmd())
    else:
        try:
            winreg.DeleteValue(key, _STARTUP_APP_NAME)
        except OSError:
            pass
    winreg.CloseKey(key)


class TrayApp:
    def __init__(self):
        self.config = Config()
        self.tts = GoogleTTS(self.config)
        self.player = AudioPlayer()
        self._reading = False
        self._settings_open = False

        # Root tkinter oculto (para manejar ventanas de diálogo en el hilo principal)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("TTS Reader")

        self.icon = pystray.Icon(
            "tts_tray",
            icon=_make_icon(),
            title="TTS Reader",
            menu=pystray.Menu(
                pystray.MenuItem("Configuración", self._menu_settings, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Iniciar con Windows",
                    self._menu_toggle_startup,
                    checked=lambda _: _is_startup_enabled(),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Detener audio", self._menu_stop),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Salir", self._menu_exit),
            ),
        )

    # ── hotkey ──────────────────────────────────────────────

    def _register_hotkey(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        try:
            keyboard.add_hotkey(self.config.hotkey, self._hotkey_cb, suppress=False)
        except Exception as e:
            print(f"No se pudo registrar hotkey '{self.config.hotkey}': {e}", file=sys.stderr)

    def _hotkey_cb(self):
        if self._reading:
            return
        self._reading = True
        threading.Thread(target=self._do_read, daemon=True).start()

    def _do_read(self):
        try:
            # Marcador para detectar si Ctrl+C realmente copió algo
            marker = f"__TTS_{uuid.uuid4()}__"
            try:
                old = pyperclip.paste()
            except Exception:
                old = ""

            pyperclip.copy(marker)

            # Soltar los modificadores del hotkey (ej: Ctrl, Alt) ANTES de
            # enviar Ctrl+C, para que no se combinen y formen Ctrl+Alt+C.
            for _mod in ("alt", "ctrl", "shift", "right alt", "left alt"):
                try:
                    keyboard.release(_mod)
                except Exception:
                    pass
            time.sleep(0.08)

            keyboard.send("ctrl+c")
            time.sleep(0.25)

            try:
                text = pyperclip.paste()
            except Exception:
                text = marker

            # Restaurar clipboard original
            try:
                pyperclip.copy(old)
            except Exception:
                pass

            if text == marker or not text.strip():
                return  # Nada seleccionado

            mp3 = self.tts.synthesize(text.strip())
            self.player.play(mp3, speed=self.config.speaking_rate)

        except ValueError as e:
            # API key no configurada
            self._notify("TTS Reader", str(e))
            self.root.after(0, self._open_settings)
        except APINotEnabledError as e:
            self._notify("TTS Reader", "La API de Text-to-Speech no está habilitada. Abrí Configuración.")
            self.root.after(0, lambda: _show_api_not_enabled(self.root, e.enable_url))
        except Exception as e:
            self._notify("TTS Reader — Error", str(e)[:120])
        finally:
            self._reading = False

    # ── menú tray ────────────────────────────────────────────

    def _menu_settings(self, *_):
        self.root.after(0, self._open_settings)

    def _menu_toggle_startup(self, *_):
        _set_startup(not _is_startup_enabled())

    def _menu_stop(self, *_):
        self.player.stop()

    def _menu_exit(self, *_):
        self.player.stop()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self.icon.stop()
        self.root.quit()

    def _notify(self, title, msg):
        try:
            self.icon.notify(msg, title)
        except Exception:
            pass

    # ── settings ────────────────────────────────────────────

    def _open_settings(self):
        if self._settings_open:
            return
        self._settings_open = True
        dlg = SettingsWindow(self.root, self.config, self.tts, self.player)
        dlg.window.wait_window()
        self._settings_open = False
        self._register_hotkey()  # Re-registrar por si cambió el shortcut

    # ── run ─────────────────────────────────────────────────

    def run(self):
        self._register_hotkey()
        threading.Thread(target=self.icon.run, daemon=True).start()
        # Hilo principal: event loop de tkinter
        self.root.mainloop()


# ──────────────────────────────────────────────────────────────
# VENTANA DE TUTORIAL
# ──────────────────────────────────────────────────────────────

TUTORIAL_STEPS = [
    (
        "1",
        "Crear una cuenta de Google (si no tenés)",
        "Necesitás una cuenta Google normal (Gmail, etc.).\n"
        "El servicio TTS tiene 1 millón de caracteres gratis por mes,\n"
        "más que suficiente para uso personal.",
        None,
    ),
    (
        "2",
        "Ir a Google Cloud Console y crear un proyecto",
        "Hacé clic en el botón para abrir Google Cloud Console.\n"
        "Si es la primera vez, aceptá los términos.\n"
        "Arriba a la izquierda, hacé clic en el selector de proyectos\n"
        "→ \"Nuevo proyecto\" → ponele cualquier nombre → Crear.",
        "https://console.cloud.google.com/projectcreate",
    ),
    (
        "3",
        "Activar la API de Text-to-Speech",
        "Hacé clic para abrir la página de la API.\n"
        "Asegurate de tener seleccionado tu proyecto (arriba a la izquierda).\n"
        "Hacé clic en el botón azul \"Habilitar\".",
        "https://console.cloud.google.com/apis/library/texttospeech.googleapis.com",
    ),
    (
        "4",
        "Crear la API Key",
        "Hacé clic para ir a Credenciales.\n"
        "Hacé clic en \"+ Crear credenciales\" → \"Clave de API\".\n"
        "Se genera una clave. Copiala.",
        "https://console.cloud.google.com/apis/credentials",
    ),
    (
        "5",
        "Pegar la API Key en Configuración",
        "Volvé a la ventana de Configuración de TTS Reader,\n"
        "pegá la clave en el campo \"API Key\" y hacé clic en\n"
        "\"Probar voz\" para verificar que funciona.",
        None,
    ),
]


class TutorialWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Cómo obtener la API Key de Google Cloud TTS")
        self.window.resizable(False, False)
        self.window.grab_set()
        self.window.focus_force()
        self._build()
        self._center()

    def _build(self):
        outer = ttk.Frame(self.window, padding=20)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="Tutorial: Obtener API Key de Google Cloud TTS",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        ttk.Label(
            outer,
            text="El servicio es gratuito hasta 1 millón de caracteres por mes (uso personal normal).",
            foreground="#555",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(0, 14))

        for num, title, desc, url in TUTORIAL_STEPS:
            step_frame = ttk.Frame(outer, relief="solid", borderwidth=1)
            step_frame.pack(fill="x", pady=4)

            inner = ttk.Frame(step_frame, padding=(10, 8))
            inner.pack(fill="x")

            # Número y título en la misma línea
            header = ttk.Frame(inner)
            header.pack(fill="x", anchor="w")

            badge = tk.Label(
                header,
                text=f" {num} ",
                background="#1a73e8",
                foreground="white",
                font=("Segoe UI", 9, "bold"),
                padx=4,
            )
            badge.pack(side="left", padx=(0, 8))

            ttk.Label(
                header,
                text=title,
                font=("Segoe UI", 9, "bold"),
            ).pack(side="left")

            # Descripción
            ttk.Label(
                inner,
                text=desc,
                foreground="#333",
                font=("Segoe UI", 8),
                justify="left",
            ).pack(anchor="w", padx=(0, 0), pady=(4, 0))

            # Botón link (si hay URL)
            if url:
                btn_text = "Abrir en el navegador →"
                lnk = tk.Label(
                    inner,
                    text=btn_text,
                    foreground="#1a73e8",
                    font=("Segoe UI", 8, "underline"),
                    cursor="hand2",
                )
                lnk.pack(anchor="w", pady=(4, 0))
                lnk.bind("<Button-1>", lambda _, u=url: webbrowser.open(u))

        ttk.Separator(outer).pack(fill="x", pady=12)
        ttk.Button(outer, text="Cerrar", command=self.window.destroy).pack(anchor="e")

    def _center(self):
        self.window.update_idletasks()
        w  = self.window.winfo_width()
        h  = self.window.winfo_height()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        self.window.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


# ──────────────────────────────────────────────────────────────
# VENTANA DE CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────

class SettingsWindow:
    def __init__(self, parent, config: Config, tts: GoogleTTS, player: AudioPlayer):
        self.config = config
        self.tts = tts
        self.player = player
        self._capturing = False

        self.window = tk.Toplevel(parent)
        self.window.title("TTS Reader — Configuración")
        self.window.resizable(False, False)
        self.window.grab_set()
        self.window.focus_force()

        self._build()
        self._center()

    def _build(self):
        f = ttk.Frame(self.window, padding=18)
        f.pack(fill="both", expand=True)

        row = 0

        # ── API Key ──────────────────────────────────────────
        ttk.Label(f, text="Google Cloud API Key:", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        row += 1

        self._key_var = tk.StringVar(value=self.config.api_key)
        key_entry = ttk.Entry(f, textvariable=self._key_var, width=44, show="•")
        key_entry.grid(row=row, column=0, columnspan=2, sticky="ew")

        self._show_key = tk.BooleanVar()
        ttk.Checkbutton(
            f, text="Ver",
            variable=self._show_key,
            command=lambda: key_entry.config(show="" if self._show_key.get() else "•"),
        ).grid(row=row, column=2, sticky="w", padx=(6, 0))
        row += 1

        ttk.Button(f, text="¿Cómo consigo la API Key? Ver tutorial →",
                   command=lambda: TutorialWindow(self.window)).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(2, 10))
        row += 1

        ttk.Separator(f).grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
        row += 1

        # ── Voz ──────────────────────────────────────────────
        ttk.Label(f, text="Voz:", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        row += 1

        labels = [lbl for _, _, lbl in VOICES]
        names  = [nm  for nm, _, _ in VOICES]
        cur_idx = next((i for i, (n, _, _) in enumerate(VOICES) if n == self.config.voice_name), 0)

        self._voice_var    = tk.StringVar(value=labels[cur_idx])
        self._voice_names  = names
        self._voice_labels = labels

        ttk.Combobox(f, textvariable=self._voice_var, values=labels, state="readonly", width=44).grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10)
        )
        row += 1

        ttk.Separator(f).grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
        row += 1

        # ── Velocidad ────────────────────────────────────────
        ttk.Label(f, text="Velocidad:", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, sticky="w"
        )
        self._speed_var = tk.DoubleVar(value=self.config.speaking_rate)
        self._speed_entry_var = tk.StringVar(value=f"{self.config.speaking_rate:.2f}")

        speed_entry = ttk.Entry(f, textvariable=self._speed_entry_var, width=6, justify="center")
        speed_entry.grid(row=row, column=2, sticky="e")
        row += 1

        speed_slider = tk.Scale(
            f, from_=0.5, to=4.0, resolution=0.1, variable=self._speed_var,
            orient="horizontal", length=310, showvalue=False,
            command=lambda v: self._speed_entry_var.set(f"{float(v):.2f}"),
        )
        speed_slider.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(2, 10))
        row += 1

        def _speed_entry_apply(event=None):
            try:
                v = float(self._speed_entry_var.get().replace(",", "."))
                v = max(0.5, min(4.0, round(v, 2)))
                self._speed_var.set(v)
                self._speed_entry_var.set(f"{v:.2f}")
            except ValueError:
                self._speed_entry_var.set(f"{self._speed_var.get():.2f}")

        speed_entry.bind("<Return>", _speed_entry_apply)
        speed_entry.bind("<FocusOut>", _speed_entry_apply)

        # ── Tono ─────────────────────────────────────────────
        ttk.Label(f, text="Tono (semitonos):", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, sticky="w"
        )
        self._pitch_lbl = ttk.Label(f, text=f"{self.config.pitch:+.1f}", width=6, anchor="e")
        self._pitch_lbl.grid(row=row, column=2, sticky="e")
        row += 1

        self._pitch_var = tk.DoubleVar(value=self.config.pitch)
        ttk.Scale(
            f, from_=-10.0, to=10.0, variable=self._pitch_var, orient="horizontal", length=340,
            command=lambda v: self._pitch_lbl.config(text=f"{float(v):+.1f}"),
        ).grid(row=row, column=0, columnspan=3, sticky="ew", pady=(2, 10))
        row += 1

        ttk.Separator(f).grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
        row += 1

        # ── Shortcut ─────────────────────────────────────────
        ttk.Label(f, text="Shortcut global:", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        row += 1

        hf = ttk.Frame(f)
        hf.grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self._hk_var = tk.StringVar(value=self.config.hotkey)
        self._hk_entry = ttk.Entry(hf, textvariable=self._hk_var, width=22, state="readonly")
        self._hk_entry.pack(side="left", padx=(0, 6))

        self._cap_btn = ttk.Button(hf, text="Cambiar…", command=self._start_capture)
        self._cap_btn.pack(side="left")

        self._cap_lbl = ttk.Label(hf, text="", foreground="#666", width=18)
        self._cap_lbl.pack(side="left", padx=6)
        row += 1

        ttk.Separator(f).grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
        row += 1

        # ── Botones ──────────────────────────────────────────
        bf = ttk.Frame(f)
        bf.grid(row=row, column=0, columnspan=3, sticky="ew")

        ttk.Button(bf, text="Probar voz", command=self._test).pack(side="left")
        ttk.Button(bf, text="Guardar",    command=self._save).pack(side="right", padx=(6, 0))
        ttk.Button(bf, text="Cancelar",   command=self.window.destroy).pack(side="right")

    # ── captura de shortcut ──────────────────────────────────

    def _start_capture(self):
        self._capturing = True
        self._cap_lbl.config(text="Presioná la combinación…", foreground="steelblue")
        self._cap_btn.config(state="disabled")
        self._hk_entry.config(state="normal")
        self._hk_var.set("")
        self._hk_entry.config(state="readonly")
        self.window.bind("<KeyPress>", self._on_key)

    def _on_key(self, ev):
        if not self._capturing:
            return
        ignore = {
            "control_l", "control_r", "shift_l", "shift_r",
            "alt_l", "alt_r", "super_l", "super_r",
            "control", "shift", "alt", "meta",
        }
        key = ev.keysym.lower()
        if key in ignore:
            return

        parts = []
        if ev.state & 0x4: parts.append("ctrl")
        if ev.state & 0x1: parts.append("shift")
        if ev.state & 0x8: parts.append("alt")
        parts.append(key)
        combo = "+".join(parts)

        self._hk_entry.config(state="normal")
        self._hk_var.set(combo)
        self._hk_entry.config(state="readonly")
        self._capturing = False
        self._cap_lbl.config(text="✓ Listo", foreground="green")
        self._cap_btn.config(state="normal")
        self.window.unbind("<KeyPress>")

    # ── helpers ──────────────────────────────────────────────

    def _get_speed(self) -> float:
        try:
            v = float(self._speed_entry_var.get().replace(",", "."))
            return max(0.5, min(4.0, round(v, 2)))
        except ValueError:
            return round(self._speed_var.get(), 2)

    # ── test / save ──────────────────────────────────────────

    def _test(self):
        api_key = self._key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Sin API Key", "Ingresá una API key primero.", parent=self.window)
            return

        idx = self._voice_labels.index(self._voice_var.get())
        cfg_test = Config()
        cfg_test._d.update({
            "api_key": api_key,
            "voice_name": self._voice_names[idx],
            "speaking_rate": self._get_speed(),
            "pitch": round(self._pitch_var.get(), 2),
        })
        tts_test = GoogleTTS(cfg_test)

        def _run():
            try:
                mp3 = tts_test.synthesize("Hola, esta es la voz de prueba de Google TTS.")
                self.player.play(mp3, speed=cfg_test.speaking_rate)
            except APINotEnabledError as e:
                self.window.after(0, lambda: _show_api_not_enabled(self.window, e.enable_url))
            except Exception as e:
                self.window.after(0, lambda: messagebox.showerror("Error", str(e), parent=self.window))

        threading.Thread(target=_run, daemon=True).start()

    def _save(self):
        idx = self._voice_labels.index(self._voice_var.get())
        self.config.api_key      = self._key_var.get().strip()
        self.config.voice_name   = self._voice_names[idx]
        self.config.speaking_rate = self._get_speed()
        self.config.pitch        = round(self._pitch_var.get(), 2)
        hk = self._hk_var.get().strip()
        if hk:
            self.config.hotkey = hk
        self.config.save()
        messagebox.showinfo("Guardado", "Configuración guardada correctamente.", parent=self.window)
        self.window.destroy()

    def _center(self):
        self.window.update_idletasks()
        w  = self.window.winfo_width()
        h  = self.window.winfo_height()
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        self.window.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


# ──────────────────────────────────────────────────────────────
# ENTRADA
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = TrayApp()
    app.run()
