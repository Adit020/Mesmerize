import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox
import threading
import sqlite3
import os
import fitz
import json

from modules.voice_engine import speak, listen_command
from modules.hotword_listener import wait_for_wake_word
from ui.waveform_visualizer import WaveformVisualizer
from ui.listening_visuals import PulseVisualizer
from config.user_config import get_or_set_wake_phrase
from modules import pdf_manager

# --- DATABASE SETUP ---
conn = sqlite3.connect("mesmerizer.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        content TEXT
    )
""")
conn.commit()

# --- UI SETUP ---

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("800x650")
app.title("Mesmerizer - PDF Voice Assistant")

title_label = ctk.CTkLabel(app, text="Mesmerizer", font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(pady=10)

desc_label = ctk.CTkLabel(app, text="Upload once. Retrieve anytime. Talk to your PDFs.")
desc_label.pack()

# Pulse + Waveform container
vis_frame = ctk.CTkFrame(app)
vis_frame.pack(pady=10)

waveform = WaveformVisualizer(vis_frame)
waveform.pack(side="right", padx=20)

pulse = PulseVisualizer(vis_frame)
pulse.pack(side="left", padx=20)

# PDF Management UI
upload_btn = ctk.CTkButton(app, text="Upload PDF", command=lambda: upload_pdf())
upload_btn.pack(pady=8)

dropdown_frame = ctk.CTkFrame(app)
dropdown_frame.pack(pady=5)

file_label = ctk.CTkLabel(dropdown_frame, text="Select PDF:")
file_label.pack(side="left", padx=(0, 10))

pdf_selector = Combobox(dropdown_frame, state="readonly", width=50)
pdf_selector.pack(side="left")

load_btn = ctk.CTkButton(dropdown_frame, text="Load", command=lambda: load_pdf())
load_btn.pack(side="left", padx=5)

delete_btn = ctk.CTkButton(dropdown_frame, text="Delete", command=lambda: delete_pdf())
delete_btn.pack(side="left", padx=5)

logbox = ctk.CTkTextbox(app, width=700, height=300)
logbox.pack(pady=10)
logbox.configure(state="disabled")

def log(text):
    logbox.configure(state="normal")
    logbox.insert("end", text + "\n")
    logbox.see("end")
    logbox.configure(state="disabled")

def update_dropdown():
    cursor.execute("SELECT filename FROM pdfs ORDER BY id DESC")
    files = [row[0] for row in cursor.fetchall()]
    pdf_selector['values'] = files
    if files:
        pdf_selector.set(files[0])

def upload_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not file_path:
        return
    filename = os.path.basename(file_path)

    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (filename,))
    if cursor.fetchone():
        messagebox.showinfo("Info", f"{filename} already uploaded.")
        log(f"[DB] {filename} already exists.")
        update_dropdown()
        return

    doc = fitz.open(file_path)
    content = "\n".join([page.get_text() for page in doc])
    cursor.execute("INSERT INTO pdfs (filename, content) VALUES (?, ?)", (filename, content))
    conn.commit()

    messagebox.showinfo("Uploaded", f"{filename} stored.")
    log(f"[UPLOAD] Stored {filename}")
    update_dropdown()

def load_pdf():
    name = pdf_selector.get()
    if not name:
        messagebox.showwarning("No Selection", "Choose a file first.")
        return
    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (name,))
    content = cursor.fetchone()[0]
    logbox.configure(state="normal")
    logbox.insert("end", f"\n--- {name} ---\n{content[:2000]}\n...\n")
    logbox.configure(state="disabled")

def delete_pdf():
    name = pdf_selector.get()
    if not name:
        return
    confirm = messagebox.askyesno("Delete", f"Delete '{name}'?")
    if not confirm:
        return
    cursor.execute("DELETE FROM pdfs WHERE filename = ?", (name,))
    conn.commit()
    log(f"[DELETE] Removed {name}")
    update_dropdown()

# --- MAIN ASSISTANT FLOW ---
def assistant_thread():
    wake_phrase = get_or_set_wake_phrase()
    speak(f"Hi, I'm Mesmerizer. Say '{wake_phrase}' to start.")

    while True:
        wait_for_wake_word(wake_phrase)
        speak("Listening now.")
        pulse.start_animation()
        waveform.start_visualization()

        command = listen_command()

        pulse.stop_animation()
        waveform.stop_visualization()

        if command:
            if "upload" in command:
                speak("Opening file dialog. Please choose your PDF.")
                result = pdf_manager.upload_pdf_dialog()
                speak(result or "No file selected.")

            elif "read" in command:
                pdfs = pdf_manager.list_pdfs()
                if not pdfs:
                    speak("You don’t have any PDFs saved yet.")
                else:
                    latest = pdfs[0]
                    content = pdf_manager.get_pdf_content(latest)
                    speak(f"Reading the latest file: {latest}")
                    speak(content[:500])  # limit for TTS
                    speak("Reading truncated. You can ask for specific sections later.")

            else:
                speak("I heard: " + command)

# --- Init ---
update_dropdown()
threading.Thread(target=assistant_thread, daemon=True).start()
app.mainloop()
