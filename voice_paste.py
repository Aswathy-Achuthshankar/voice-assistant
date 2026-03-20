#!/usr/bin/env python3
"""
voice_paste — Voice-to-text paste for macOS.

Toggle recording with Right Command, transcribe with Whisper (MLX),
and paste the result into the focused text field.

Usage:
    python voice_paste.py
    python voice_paste.py --model large-v3
    python voice_paste.py --language hi
"""

import argparse
import atexit
import subprocess
import sys
import threading
import time
from enum import Enum, auto

import mlx_whisper
import numpy as np
import pyperclip
import Quartz
import sounddevice as sd
from pynput import keyboard


# ── Helpers ──────────────────────────────────────────────────────────────────

PREFIX = "[voice_paste]"


def log(msg: str = "") -> None:
    print(f"{PREFIX} {msg}" if msg else PREFIX)


# ── Audio feedback ──────────────────────────────────────────────────────────

SOUNDS = {
    "start":  "/System/Library/Sounds/Tink.aiff",
    "stop":   "/System/Library/Sounds/Pop.aiff",
    "cancel": "/System/Library/Sounds/Funk.aiff",
}


def beep(name: str) -> None:
    """Play a macOS system sound (non-blocking)."""
    path = SOUNDS.get(name)
    if path:
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


# ── State machine ────────────────────────────────────────────────────────────

class State(Enum):
    IDLE       = auto()
    RECORDING  = auto()
    PROCESSING = auto()


# ── Hotkey mapping ───────────────────────────────────────────────────────────

HOTKEY_MAP = {
    "right_cmd": keyboard.Key.cmd_r,
    "left_cmd":  keyboard.Key.cmd_l,
    "f5":        keyboard.Key.f5,
    "f6":        keyboard.Key.f6,
    "f7":        keyboard.Key.f7,
    "f8":        keyboard.Key.f8,
}

# ── MLX model name mapping ──────────────────────────────────────────────────

MLX_MODEL_MAP = {
    "turbo":    "mlx-community/whisper-large-v3-turbo",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
}


# ── Core app ─────────────────────────────────────────────────────────────────

class VoicePaste:
    SAMPLE_RATE = 16_000   # Whisper's native rate
    CHANNELS    = 1        # Mono

    def __init__(self, model_name: str, language: str, hotkey_name: str):
        self._lock   = threading.Lock()
        self._state  = State.IDLE
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._record_start: float = 0.0
        self._language = language
        self._model_path = MLX_MODEL_MAP[model_name]

        # Resolve hotkey
        self._hotkey_name = hotkey_name
        self._hotkey_key  = HOTKEY_MAP[hotkey_name]

        # Load model (warmup with 1s of silence to force download + load)
        log(f"Loading model '{model_name}' ...")
        t0 = time.monotonic()
        dummy = np.zeros(self.SAMPLE_RATE, dtype=np.float32)
        mlx_whisper.transcribe(dummy, path_or_hf_repo=self._model_path, language=language)
        elapsed = time.monotonic() - t0
        log(f"Device: Apple Silicon (MLX)")
        log(f"Model loaded in {elapsed:.1f}s")
        log(f"Language: {language}")

        log()
        self._print_ready()

        atexit.register(self._cleanup)

    # ── Status ───────────────────────────────────────────────────────────────

    def _print_ready(self) -> None:
        hotkey_label = self._hotkey_name.replace("_", " ").title()
        log(f"Ready — {hotkey_label}: record | Escape: cancel | Ctrl-C: quit")

    # ── Audio callback (sounddevice thread) ──────────────────────────────────

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if self._state is not State.RECORDING:
            return
        with self._lock:
            if self._state is State.RECORDING:
                self._frames.append(indata.copy())

    # ── Recording lifecycle ──────────────────────────────────────────────────

    def _start_recording(self) -> None:
        with self._lock:
            if self._state is not State.IDLE:
                return
            self._state  = State.RECORDING
            self._frames = []
            self._record_start = time.monotonic()

        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="float32",
            blocksize=1024,
            callback=self._audio_callback,
        )
        self._stream.start()
        beep("start")
        log("Recording ...")

    def _stop_recording(self) -> None:
        with self._lock:
            if self._state is not State.RECORDING:
                return
            self._state = State.PROCESSING
            duration = time.monotonic() - self._record_start

        self._close_stream()
        beep("stop")
        log(f"Stopped ({duration:.1f}s captured). Transcribing ...")
        threading.Thread(target=self._transcribe_and_paste, daemon=True).start()

    def _cancel_recording(self) -> None:
        with self._lock:
            if self._state is not State.RECORDING:
                return
            self._state = State.IDLE
            self._frames = []

        self._close_stream()
        beep("cancel")
        log("Cancelled.")
        log()
        self._print_ready()

    # ── Stream management ────────────────────────────────────────────────────

    def _close_stream(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

    def _cleanup(self) -> None:
        self._close_stream()

    # ── Transcription + paste ────────────────────────────────────────────────

    def _transcribe_and_paste(self) -> None:
        try:
            with self._lock:
                frames = list(self._frames)
                self._frames = []

            if not frames:
                log("No audio captured.")
                return

            audio = np.concatenate(frames, axis=0).flatten()

            t0 = time.monotonic()
            result = mlx_whisper.transcribe(
                audio,
                path_or_hf_repo=self._model_path,
                language=self._language,
            )
            elapsed = time.monotonic() - t0

            text = result.get("text", "").strip()
            if not text:
                log("No speech detected.")
                return

            log(f'Done in {elapsed:.1f}s — "{text}"')
            self._paste(text)
            log("Pasted.")

        except Exception as exc:
            log(f"Error: {exc}")

        finally:
            with self._lock:
                self._state = State.IDLE
            log()
            self._print_ready()

    def _paste(self, text: str) -> None:
        pyperclip.copy(text)
        time.sleep(0.1)

        clip = pyperclip.paste()
        if clip != text:
            log(f"WARNING: Clipboard mismatch. Expected {len(text)} chars, got {len(clip)}.")

        # Send Cmd+V via Quartz CGEventPost (key code 9 = 'v').
        source = Quartz.CGEventSourceCreate(
            Quartz.kCGEventSourceStateHIDSystemState
        )
        event = Quartz.CGEventCreateKeyboardEvent(source, 9, True)
        Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        time.sleep(0.01)
        event = Quartz.CGEventCreateKeyboardEvent(source, 9, False)
        Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    # ── Keyboard handler (pynput listener thread) ───────────────────────────

    def _on_press(self, key) -> None:
        if key == self._hotkey_key:
            state = self._state
            if state is State.IDLE:
                self._start_recording()
            elif state is State.RECORDING:
                threading.Thread(target=self._stop_recording, daemon=True).start()

        elif key == keyboard.Key.esc:
            if self._state is State.RECORDING:
                self._cancel_recording()

    # ── Entry point ──────────────────────────────────────────────────────────

    def run(self) -> None:
        try:
            with keyboard.Listener(on_press=self._on_press) as listener:
                listener.join()
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()
            log("Bye.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Voice-to-text paste for macOS (Apple Silicon, MLX).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Models:
  turbo     large-v3-turbo (faster, slightly less accurate)  [default]
  large-v3  full large-v3 (highest accuracy, slower)

Hotkeys:
  right_cmd   Right Command key   [default]
  left_cmd    Left Command key
  f5 … f8     Function keys

macOS setup (one-time):
  1. brew install portaudio ffmpeg
  2. System Settings → Privacy & Security → Accessibility → add your terminal
  3. Microphone permission is auto-prompted on first run
        """,
    )
    parser.add_argument(
        "--model",
        choices=["turbo", "large-v3"],
        default="turbo",
        help="Whisper model (default: turbo)",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code for transcription, e.g. en, hi, ta (default: en)",
    )
    parser.add_argument(
        "--hotkey",
        choices=list(HOTKEY_MAP.keys()),
        default="right_cmd",
        help="Key to toggle recording (default: right_cmd)",
    )

    args = parser.parse_args()

    app = VoicePaste(
        model_name=args.model,
        language=args.language,
        hotkey_name=args.hotkey,
    )
    app.run()


if __name__ == "__main__":
    main()
