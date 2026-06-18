from pathlib import Path
import os
import tempfile
import wave
import re

import sounddevice as sd
from scipy.io import wavfile
from piper import PiperVoice, SynthesisConfig



BASE_DIR = Path(__file__).resolve().parent
VOICE_NAME = "en_US-ryan-high"

VOICE_PATH = BASE_DIR / "voices" / f"{VOICE_NAME}.onnx"

if not VOICE_PATH.exists():
    raise FileNotFoundError(
        f"Ryan voice not found:\n{VOICE_PATH}\n"
        "Please download the Ryan voice and place it inside the voices folder."
    )

voice = PiperVoice.load(str(VOICE_PATH))



voice_config = SynthesisConfig(
    volume=1.0,
    length_scale=1.45,      
    noise_scale=0.22,        
    noise_w_scale=0.22,     
    normalize_audio=True,
)




def prepare_text(text: str) -> str:
    text = text.strip()

    replacements = {
        "AI": "A I",
        "API": "A P I",
        "CPU": "C P U",
        "GPU": "G P U",
        "RAM": "ram",
        "USB": "U S B",
        "VS Code": "Visual Studio Code",
        "GitHub": "Git Hub",
        "e.g.": "for example",
        "i.e.": "that is",
        "etc.": "etcetera",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    text = text.replace(",", ", ")

    text = text.replace(". ", ".  ")
    text = text.replace("? ", "?  ")
    text = text.replace("! ", "!  ")

   
    text = text.replace("\n\n", ".   ")

    if text and text[-1] not in ".!?":
        text += "."

    return text



def speak(text: str):

    text = prepare_text(text)

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as tmp:

            temp_path = tmp.name

        with wave.open(temp_path, "wb") as wav_file:
            voice.synthesize_wav(
                text,
                wav_file,
                syn_config=voice_config
            )

        sample_rate, audio = wavfile.read(temp_path)

        sd.play(audio, sample_rate)
        sd.wait()

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)