# modules/pdf_manager.py
import os
import fitz  # PyMuPDF
import sqlite3
from tkinter import filedialog

# --- DB CONNECTION ---
conn = sqlite3.connect("mesmerizer.db")
cursor = conn.cursor()

# --- FUNCTIONS ---
def upload_pdf_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not file_path:
        return None

    filename = os.path.basename(file_path)

    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (filename,))
    if cursor.fetchone():
        return f"'{filename}' is already uploaded."

    doc = fitz.open(file_path)
    content = "\n".join([page.get_text() for page in doc])

    cursor.execute("INSERT INTO pdfs (filename, content) VALUES (?, ?)", (filename, content))
    conn.commit()
    return f"'{filename}' uploaded and stored."

def list_pdfs():
    cursor.execute("SELECT filename FROM pdfs ORDER BY id DESC")
    return [row[0] for row in cursor.fetchall()]

def get_pdf_content(filename):
    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (filename,))
    result = cursor.fetchone()
    return result[0] if result else None

def search_pdf_content(filename, keyword):
    content = get_pdf_content(filename)
    if not content:
        return f"No content found in {filename}."

    lines = content.splitlines()
    matches = [line for line in lines if keyword.lower() in line.lower()]

    if not matches:
        return f"No matches found for '{keyword}' in {filename}."

    return "\n\n".join(matches[:5])  # Limit to 5 for brevity
