import customtkinter as ctk
import numpy as np
import sounddevice as sd
import threading
import time

class WaveformVisualizer(ctk.CTkCanvas):
    def __init__(self, master, width=300, height=150, color="#00FFD1", **kwargs):
        super().__init__(master, width=width, height=height, bg="#1F1F1F", highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.color = color
        self.running = False
        self.stream = None
        self.volume = 0

    def start_visualization(self):
        self.running = True
        self.stream = sd.InputStream(callback=self.audio_callback, channels=1, samplerate=44100)
        self.stream.start()
        threading.Thread(target=self._update_loop, daemon=True).start()

    def stop_visualization(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.delete("waveform")

    def audio_callback(self, indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        self.volume = min(volume_norm, 100)  # normalize for display

    def _update_loop(self):
        while self.running:
            self.delete("waveform")
            mid = self.height // 2
            bar_height = int(self.volume * 1.5)
            self.create_line(
                10, mid - bar_height,
                self.width - 10, mid + bar_height,
                fill=self.color, width=4, tags="waveform"
            )
            time.sleep(0.05)
