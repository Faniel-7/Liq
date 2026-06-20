import os
import tempfile
import threading
import time

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
MODEL_SIZE = "base"

# Load once when the file is imported
whisper_model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8"
)

def listen():
    audio_chunks = []
    stop_event = threading.Event()

    def wait_for_enter():
        input("Press Enter again to stop recording...")
        stop_event.set()

    def callback(indata, frames, time_info, status):
        if status:
            print(status)
        audio_chunks.append(indata.copy())

    print("\nSpeak now...")

    stopper = threading.Thread(target=wait_for_enter, daemon=True)
    stopper.start()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        callback=callback
    ):
        while not stop_event.is_set():
            time.sleep(0.05)

    if not audio_chunks:
        return ""

    audio = np.concatenate(audio_chunks, axis=0)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        temp_path = tmp.name

    try:
        wavfile.write(temp_path, SAMPLE_RATE, audio)

        segments, info = whisper_model.transcribe(
            temp_path,
            language="en",
            beam_size=1,
            vad_filter=True
        )

        text_parts = []
        for segment in segments:
            part = segment.text.strip()
            if part:
                text_parts.append(part)

        return " ".join(text_parts).strip()

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)