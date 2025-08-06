import customtkinter as ctk
import threading
import time

class PulseVisualizer(ctk.CTkCanvas):
    def __init__(self, master, width=150, height=150, pulse_color="#00FFD1", **kwargs):
        super().__init__(master, width=width, height=height, bg="#1F1F1F", highlightthickness=0, **kwargs)
        self.pulse_color = pulse_color
        self.center = width // 2
        self.base_circle = self.create_oval(
            self.center - 40, self.center - 40,
            self.center + 40, self.center + 40,
            outline=self.pulse_color, width=4
        )
        self.animating = False
        self.rings = []

    def start_animation(self):
        if not self.animating:
            self.animating = True
            threading.Thread(target=self._animate_loop, daemon=True).start()

    def stop_animation(self):
        self.animating = False
        self.delete("pulse_ring")
        self.rings.clear()

    def _animate_loop(self):
        while self.animating:
            ring = self.create_oval(
                self.center - 30, self.center - 30,
                self.center + 30, self.center + 30,
                outline=self.pulse_color, width=2, tags="pulse_ring"
            )
            self.rings.append(ring)
            self._expand_ring(ring, 0)
            time.sleep(0.4)

    def _expand_ring(self, ring, size):
        if not self.animating or size > 60:
            self.delete(ring)
            if ring in self.rings:
                self.rings.remove(ring)
            return

        new_coords = (
            self.center - (30 + size),
            self.center - (30 + size),
            self.center + (30 + size),
            self.center + (30 + size)
        )
        alpha = max(0, 255 - int(size * 4))
        hex_alpha = f'{alpha:02x}'
        color = f"{self.pulse_color}{hex_alpha}"
        try:
            self.coords(ring, *new_coords)
            self.itemconfig(ring, outline=color)
        except:
            pass
        self.after(40, lambda: self._expand_ring(ring, size + 2))
