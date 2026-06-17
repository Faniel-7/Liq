from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import wave

import sounddevice as sd
from scipy.io import wavfile

BASE_DIR = Path(__file__).resolve().parent

# Change this to whichever Piper voice you want to try:
# "en_US-ryan-high"
# "en_US-libritts_r-medium"
# "en_US-lessac-medium"
VOICE_NAME = "en_US-lessac-medium"

VOICE_ONNX = BASE_DIR / "voices" / f"{VOICE_NAME}.onnx"
VOICE_JSON = BASE_DIR / "voices" / f"{VOICE_NAME}.onnx.json"

_piper_voice = None
_piper_checked = False


def _load_piper():
    global _piper_voice, _piper_checked

    if _piper_checked:
        return _piper_voice is not None

    _piper_checked = True

    try:
        from piper import PiperVoice, SynthesisConfig
    except Exception as e:
        print(f"Piper is not available: {e}")
        _piper_voice = None
        return False

    if not VOICE_ONNX.exists():
        print(f"Piper voice file not found: {VOICE_ONNX}")
        _piper_voice = None
        return False

    if not VOICE_JSON.exists():
        print(f"Piper config file not found: {VOICE_JSON}")
        _piper_voice = None
        return False

    try:
        _piper_voice = PiperVoice.load(str(VOICE_ONNX))
        return True
    except Exception as e:
        print(f"Piper voice failed to load: {e}")
        _piper_voice = None
        return False


def _speak_with_piper(text):
    from piper import SynthesisConfig

    config = SynthesisConfig(
        volume=1.0,
        length_scale=1.1,
        noise_scale=0.35,
        noise_w_scale=0.35,
        normalize_audio=True,
    )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        with wave.open(tmp_path, "wb") as wav_file:
            _piper_voice.synthesize_wav(text, wav_file, syn_config=config)

        sample_rate, audio = wavfile.read(tmp_path)
        sd.play(audio, sample_rate)
        sd.wait()

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def _speak_with_espeak(text):
    if shutil.which("espeak-ng") is None:
        raise RuntimeError("espeak-ng is not installed.")

    # Lower pitch + slightly slower speed for a deeper feel
    subprocess.run(
        ["espeak-ng", "-v", "en-us", "-s", "145", "-p", "35", text],
        check=True
    )


def speak(text):
    text = (text or "").strip()
    if not text:
        return

    if _load_piper():
        try:
            _speak_with_piper(text)
            return
        except Exception as e:
            print(f"Piper failed, using fallback voice: {e}")

    _speak_with_espeak(text)