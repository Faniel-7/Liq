import os
import tempfile

import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURATION = 5

whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

def listen():
    print("🎤 Listening... speak now.")
    print(f"Recording for {DURATION} seconds...")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        temp_path = tmp_file.name

    write(temp_path, SAMPLE_RATE, audio)

    segments, info = whisper_model.transcribe(
        temp_path,
        language="en",
        beam_size=1,
        vad_filter=True
    )

    text_parts = []
    for segment in segments:
        text_parts.append(segment.text.strip())

    os.remove(temp_path)

    return " ".join(text_parts).strip()