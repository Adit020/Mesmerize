import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
from modules.voice_engine import speak
import os

model_path = os.path.join(os.path.dirname(__file__), "..", "models", "vosk-model-small-en-in-0.4")
model = Model(model_path)
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def wait_for_wake_word(wake_phrase="hey mesmerizer"):
    samplerate = 16000
    device = None  # default mic
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        rec = KaldiRecognizer(model, samplerate)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()
                print(f"[Wake Listen] Heard: {text}")
                if wake_phrase.lower() in text:
                    return