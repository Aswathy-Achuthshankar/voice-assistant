# voice_paste

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-3776AB.svg)](https://www.python.org/)
[![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-000000.svg)](https://support.apple.com/en-us/116943)
[![Offline](https://img.shields.io/badge/Privacy-100%25%20Offline-green.svg)](#)

Press a hotkey, speak, and the transcribed text appears wherever your cursor is. Works in any app — Slack, VS Code, Google Docs, terminal, anything.

100% local. No cloud. No API keys. Runs entirely on your Mac using [Whisper](https://github.com/openai/whisper) via [MLX](https://github.com/ml-explore/mlx).

<!-- TODO: Add demo GIF here -->
<!-- ![Demo](docs/demo.gif) -->

## Why voice_paste over Apple Dictation?

Apple's built-in dictation works for basics. voice_paste uses **Whisper large-v3-turbo**, which handles real-world speech significantly better.

| | Apple Dictation | voice_paste |
|--|:-:|:-:|
| Languages | ~30 | 99+ |
| Accents & mixed languages | Limited | Strong (e.g. English + Hindi mid-sentence) |
| Noisy environments | Average | Trained on 680k hours of diverse audio |
| Privacy | Audio sent to Apple servers | Audio never leaves your machine |
| Customizable | No | Swap models, change language, pick your hotkey |
| Cost | Free (with Apple ID) | Free forever, no account needed |
| Works offline | Partial | Fully offline after first model download |
| Open source | No | Yes |

## How it works

```
IDLE ──[Right Cmd]──> RECORDING ──[Right Cmd]──> PROCESSING ──> IDLE
                          |                       (hotkey ignored)
                       [Escape]
                          |
                          v
                        IDLE (audio discarded)
```

1. App sits idle — zero CPU, no mic access
2. Press **Right Command** — mic opens, recording starts (you hear a click)
3. Speak
4. Press **Right Command** — mic closes, Whisper transcribes the audio
5. Transcribed text is pasted into the focused app
6. Back to idle

Press **Escape** during recording to cancel. Press **Ctrl-C** to quit.

## Requirements

- macOS on Apple Silicon (M1 / M2 / M3 / M4 / M5)
- Python 3.13 (not 3.14 — PyTorch doesn't support it yet)
- Homebrew
- ~4 GB RAM while running
- ~1.6 GB disk for the default model (downloaded once, cached locally)

## Installation

### Step 1: Install prerequisites

Make sure you have Homebrew and Python 3.13 installed.

```bash
# Install Homebrew (skip if already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.13 (skip if already installed)
brew install python@3.13

# Verify
python3.13 --version   # Should show Python 3.13.x
```

### Step 2: Clone the repository

```bash
git clone https://github.com/Aswathy-Achuthshankar/voice-assistant.git
cd voice-assistant
```

### Step 3: Run the setup script

```bash
chmod +x setup.sh
./setup.sh
```

This will automatically:
- Install system dependencies (`portaudio` for mic access, `ffmpeg` for audio processing) via Homebrew
- Create a Python virtual environment (`venv/`)
- Install all Python packages (`mlx-whisper`, `sounddevice`, `numpy`, `pyperclip`, `pynput`)

### Step 4: Grant macOS permissions (one-time)

Two permissions are needed. Without these, the app won't work.

**Microphone access:**
- You'll be prompted automatically on first run
- Click **Allow** when the dialog appears

**Accessibility access (required for hotkey + paste):**
1. Open **System Settings**
2. Go to **Privacy & Security → Accessibility**
3. Click the **+** button
4. Add your terminal app (Terminal, iTerm2, VS Code, Warp, etc.)
5. Make sure the toggle is **ON**
6. **Restart your terminal** after granting permission

> Without Accessibility permission, the hotkey listener and auto-paste (Cmd+V simulation) will silently fail.

### Step 5: Run

```bash
source venv/bin/activate

# Use the full large-v3 model (more accurate, ~3.1 GB download) RECOMMENDED
python voice_paste.py --model large-v3

# or use Default: turbo model (faster, ~1.6 GB download)
python voice_paste.py
```

The first run downloads the Whisper model. This happens once — after that the model is cached locally at `~/.cache/huggingface/` and everything works offline.

You should see:
```
[voice_paste] Loading model 'turbo' ...
[voice_paste] Device: Apple Silicon (MLX)
[voice_paste] Model loaded in 3.2s
[voice_paste] Language: en
[voice_paste]
[voice_paste] Ready — Right Cmd: record | Escape: cancel | Ctrl-C: quit
```

### Quick start (after setup is done)

Every time you want to use it:
```bash
cd voice-assistant
source venv/bin/activate
python voice_paste.py --model large-v3 # higher accuracy
```

## Usage

```bash
source venv/bin/activate
python voice_paste.py --model large-v3
```

The first run downloads the Whisper model (~1.6 GB for turbo). Subsequent runs load from cache in `~/.cache/huggingface/`.

### Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--model` | `turbo`, `large-v3` | `turbo` | Whisper model to use |
| `--language` | Any [ISO 639-1 code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) | `en` | Transcription language |
| `--hotkey` | `right_cmd`, `left_cmd`, `f5`–`f8` | `right_cmd` | Key to toggle recording |

### Examples

```bash
# Full large-v3 model for maximum accuracy
python voice_paste.py --model large-v3

# Default: turbo model, English, Right Command key
python voice_paste.py

# Hindi transcription
python voice_paste.py --language hi

# Tamil transcription with F5 as hotkey
python voice_paste.py --language ta --hotkey f5

# Spanish with Left Command
python voice_paste.py --language es --hotkey left_cmd
```

## Models

Models are downloaded from HuggingFace on first use and cached in `~/.cache/huggingface/`.

| Model | HuggingFace repo | Size | Speed (30s audio) | Best for |
|-------|-----------------|------|-------------------|----------|
| `turbo` | `mlx-community/whisper-large-v3-turbo` | ~1.6 GB | ~1–1.5s | Daily use, fast results |
| `large-v3` | `mlx-community/whisper-large-v3-mlx` | ~3.1 GB | ~3–5s | Maximum accuracy, complex audio |

Speeds measured on Apple M5. M1/M2 will be slightly slower but still very usable.

## Supported Languages

Whisper supports 99+ languages. Some commonly used ones:

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| `en` | English | `hi` | Hindi | `zh` | Chinese |
| `es` | Spanish | `ta` | Tamil | `ja` | Japanese |
| `fr` | French | `te` | Telugu | `ko` | Korean |
| `de` | German | `ml` | Malayalam | `ar` | Arabic |
| `pt` | Portuguese | `kn` | Kannada | `ru` | Russian |

Full list: [Whisper language codes](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py#L10)

## Tech Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| Transcription | [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) | Whisper optimized for Apple Silicon via MLX |
| Audio capture | [sounddevice](https://python-sounddevice.readthedocs.io/) | Record at 16kHz mono (Whisper's native format) |
| Hotkeys | [pynput](https://pynput.readthedocs.io/) | Global keyboard listener |
| Paste | pyperclip + Quartz CGEventPost | Clipboard management + simulate Cmd+V |
| Audio feedback | macOS system sounds via `afplay` | Click on start/stop/cancel |

## Troubleshooting

### "Hotkey not working"
You need to grant Accessibility permission to your terminal app:
`System Settings → Privacy & Security → Accessibility` → add Terminal / iTerm2 / VS Code.
Restart the app after granting permission.

### "Paste not working"
Same as above — Accessibility permission is required for simulating Cmd+V. Also make sure a text field is focused when you stop recording.

### "No speech detected"
- Check that your microphone is working (`System Settings → Sound → Input`)
- Speak clearly and close to the mic
- Try a quieter environment
- Try `--model large-v3` for better accuracy

### "Model download fails"
The model is downloaded from HuggingFace. Make sure you have internet on first run. After that, everything is cached locally and works offline. If the download is interrupted, delete `~/.cache/huggingface/` and try again.

### "High memory usage"
The turbo model uses ~4 GB RAM. If that's too much, a future update will add smaller models (tiny, small, medium). For now, close the app when not in use — it has zero background cost when not running.

### "Wrong language transcribed"
Always specify your language explicitly with `--language`. Auto-detection is coming in a future update, but for now Whisper performs best when told which language to expect.

## Comparison with Alternatives

| Feature | voice_paste | Apple Dictation | Google Voice Typing | Whisper.cpp |
|---------|:-----------:|:---------------:|:-------------------:|:-----------:|
| Offline | Yes | Partial | No | Yes |
| Privacy | Full | Partial | No | Full |
| Languages | 99+ | ~30 | ~125 | 99+ |
| Works in any app | Yes | Yes | Browser only | CLI only |
| Hotkey paste | Yes | Yes | No | No |
| Open source | Yes | No | No | Yes |
| Apple Silicon optimized | Yes (MLX) | Yes | N/A | Yes (Metal) |
| Setup effort | 1 command | Built-in | None | Build from source |

## Project Structure

```
voice-assistant/
├── voice_paste.py      # Main application
├── setup.sh            # One-command setup
├── requirements.txt    # Python dependencies
├── README.md
├── LICENSE
└── venv/               # Python virtual environment (created by setup.sh)
```

## Roadmap

- [ ] Auto-language detection (let Whisper figure out the language)
- [ ] Menu bar icon showing recording state
- [ ] Clipboard restoration (save/restore previous clipboard content)
- [ ] Configuration file (`~/.voice_paste.toml`) for persistent settings
- [ ] Transcription history log
- [ ] Auto-start on login via LaunchAgent
- [ ] Smaller model options (tiny, small, medium) for lower RAM usage
- [ ] Homebrew formula (`brew install voice-assistant`)
- [ ] pip install support (`pip install voice-assistant`)

## Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test locally (`python voice_paste.py`)
5. Submit a pull request

If you find a bug or have a feature request, please [open an issue](https://github.com/Aswathy-Achuthshankar/voice-assistant/issues).

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) — the speech recognition model
- [MLX](https://github.com/ml-explore/mlx) — Apple's machine learning framework
- [mlx-community](https://huggingface.co/mlx-community) — MLX-optimized model weights on HuggingFace

## Author

**Aswathy Achuthshankar** — [GitHub](https://github.com/Aswathy-Achuthshankar)

## License

MIT License. See [LICENSE](LICENSE) for details.
