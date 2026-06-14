import sounddevice as sd
from scipy.io.wavfile import write
import os

SAMPLE_RATE = 16000
DURATION = 5  # seconds
OUTPUT_FILE = "data/mic_test.wav"

def record_audio():
    os.makedirs("data", exist_ok=True)

    print(f"Recording for {DURATION} seconds...")
    print("Speak now.")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(OUTPUT_FILE, SAMPLE_RATE, audio)
    print(f"Saved recording to {OUTPUT_FILE}")

if __name__ == "__main__":
    record_audio()