import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, ttk
import sqlite3
import os
import fitz 
import pyttsx3
import speech_recognition as sr
import threading
import time

# ---------- INITIAL SETUP ----------

#initialize tts engine for text-to-speech
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

# ---------- DATABASE SETUP ----------

conn = sqlite3.connect('mesmerizer.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        content TEXT
    )
''')
conn.commit()

# ---------- FUNCTION ----------

def start_voice_session():
    time.sleep(1.5)  # Give time for UI to initialize
    speak("Hello, I'm Mesmerizer.")
    speak("Would you like to upload a new PDF or access an existing one?")

    response = listen_to_user()

    if response:
        if "upload" in response:
            speak("Opening upload dialog.")
            root.after(0, upload_pdf)
        elif "access" in response or "open" in response:
            cursor.execute("SELECT filename FROM pdfs")
            files = [row[0] for row in cursor.fetchall()]
            if files:
                speak(f"You have {len(files)} files.")
                speak("Available files are " + ", ".join(files[:3]))
                speak("You can choose one from the dropdown.")
                root.after(0, update_dropdown)
            else:
                speak("No PDFs are stored yet.")
        else:
            speak("Sorry, I didn't understand that. You can try again or use the buttons.")
    else:
        speak("Please use the buttons to upload or access a PDF.")

def listen_to_user():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.5)  # Noise cancellation
        show_listening(True)
        speak("I'm listening.")
        try:
            audio = recognizer.listen(source, timeout=7)
            query = recognizer.recognize_google(audio).lower()
            show_listening(False)
            return query
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
        except sr.RequestError:
            speak("There was a network error.")
        finally:
            show_listening(False)
    return None

# ---------- GUI FUNCTIONS ----------

def upload_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not file_path:
        return

    filename = os.path.basename(file_path)

    # Check if already uploaded
    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (filename,))
    result = cursor.fetchone()
    if result:
        messagebox.showinfo("Info", f"'{filename}' already uploaded.")
        log(f"[DB LOAD] {filename} already exists.")
        update_dropdown()
        return

    try:
        doc = fitz.open(file_path)
        content = ""
        for page in doc:
            content += page.get_text()

        # Insert into DB
        cursor.execute("INSERT INTO pdfs (filename, content) VALUES (?, ?)", (filename, content))
        conn.commit()

        messagebox.showinfo("Success", f"'{filename}' uploaded and stored.")
        log(f"[UPLOAD] {filename} stored successfully.")
        update_dropdown()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to upload PDF: {str(e)}")

def load_selected_pdf():
    selected_file = pdf_selector.get()
    if not selected_file:
        messagebox.showwarning("Warning", "No PDF selected.")
        return

    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (selected_file,))
    result = cursor.fetchone()
    if result:
        content = result[0]
        log_display.config(state='normal')
        log_display.insert(tk.END, f"\n--- Loaded: {selected_file} ---\n\n")
        log_display.insert(tk.END, content[:2000] + "\n...\n[Content truncated for preview]\n")  # Preview
        log_display.config(state='disabled')
    else:
        messagebox.showerror("Error", f"No content found for {selected_file}.")

def remove_selected_pdf():
    selected_file = pdf_selector.get()
    if not selected_file:
        messagebox.showwarning("Warning", "No PDF selected.")
        return

    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{selected_file}'?")
    if not confirm:
        return

    try:
        cursor.execute("DELETE FROM pdfs WHERE filename = ?", (selected_file,))
        conn.commit()
        messagebox.showinfo("Deleted", f"'{selected_file}' has been removed.")
        log(f"[DELETE] Removed PDF: {selected_file}")
        update_dropdown()
        log_display.config(state='normal')
        log_display.insert(tk.END, "\n[INFO] Please select another file.\n")
        log_display.config(state='disabled')
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete PDF: {str(e)}")

def update_dropdown():
    cursor.execute("SELECT filename FROM pdfs ORDER BY id DESC")
    files = [row[0] for row in cursor.fetchall()]
    pdf_selector['values'] = files
    if files:
        pdf_selector.set(files[0])

def log(text):
    log_display.config(state='normal')
    log_display.insert(tk.END, text + "\n")
    log_display.config(state='disabled')

def show_listening(is_listening):
    if is_listening:
        canvas.itemconfig(circle, fill="#00FFD1")
        pulse_circle()
    else:
        canvas.itemconfig(circle, fill="#444444")

def pulse_circle():
    current_color = canvas.itemcget(circle, "fill")
    next_color = "#00AA88" if current_color == "#00FFD1" else "#00FFD1"
    canvas.itemconfig(circle, fill=next_color)
    root.after(500, pulse_circle)

# ---------- MAIN UI SETUP ----------

root = tk.Tk()
root.title("Mesmerizer - PDF Voice Assistant")
root.geometry("700x600")
root.config(bg="#1F1F1F")

title_label = tk.Label(root, text="Mesmerizer", font=("Helvetica", 18, "bold"), bg="#1F1F1F", fg="#00FFD1")
title_label.pack(pady=10)

desc_label = tk.Label(root, text="Upload your PDF once. Select anytime to retrieve and continue.", bg="#1F1F1F", fg="#CCCCCC")
desc_label.pack()

canvas = tk.Canvas(root, width=100, height=100, bg="#1F1F1F", highlightthickness=0)
canvas.pack(pady=5)
circle = canvas.create_oval(20, 20, 80, 80, fill="#444444")

upload_button = tk.Button(root, text="Upload PDF", command=upload_pdf, bg="#00A8E1", fg="#FFFFFF", font=("Helvetica", 12, "bold"), width=15, height=2)
upload_button.pack(pady=10)

dropdown_frame = tk.Frame(root, bg="#1F1F1F")
dropdown_frame.pack(pady=5)

dropdown_label = tk.Label(dropdown_frame, text="Select Stored PDF:", bg="#1F1F1F", fg="white")
dropdown_label.pack(side=tk.LEFT, padx=(0,10))

pdf_selector = ttk.Combobox(dropdown_frame, width=50, state="readonly")
pdf_selector.pack(side=tk.LEFT)

load_button = tk.Button(dropdown_frame, text="Load PDF", command=load_selected_pdf, bg="#32CD32", fg="#FFFFFF", font=("Helvetica", 10, "bold"))
load_button.pack(side=tk.LEFT, padx=10)

remove_button = tk.Button(dropdown_frame, text="Remove PDF", command=remove_selected_pdf, bg="#FF4500", fg="#FFFFFF", font=("Helvetica", 10, "bold"))
remove_button.pack(side=tk.LEFT, padx=5)

log_label = tk.Label(root, text="Log Output:", bg="#1F1F1F", fg="#FFFFFF")
log_label.pack()

log_display = scrolledtext.ScrolledText(root, width=80, height=20, state='disabled', bg="#262626", fg="#00FF8F", font=("Courier", 10))
log_display.pack(pady=10)

exit_button = tk.Button(root, text="Exit", command=root.quit, bg="#FF5555", fg="#FFFFFF", font=("Helvetica", 10, "bold"), width=10)
exit_button.pack(pady=10)

# Initialize dropdown values
update_dropdown()

# ---------- START VOICE SESSION IN A SEPARATE THREAD ----------

voice_thread = threading.Thread(target=start_voice_session, daemon=True)
voice_thread.start()

root.mainloop()
