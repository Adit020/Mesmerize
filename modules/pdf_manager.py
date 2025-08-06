import os
import fitz
import sqlite3
from tkinter import filedialog

# Database connection
conn = sqlite3.connect("mesmerizer.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        content TEXT
    )
''')
conn.commit()

def upload_pdf_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if not file_path:
        return None

    filename = os.path.basename(file_path)

    # Check if already exists
    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (filename,))
    if cursor.fetchone():
        return f"'{filename}' already uploaded."

    try:
        doc = fitz.open(file_path)
        content = "\n".join([page.get_text() for page in doc])
        cursor.execute("INSERT INTO pdfs (filename, content) VALUES (?, ?)", (filename, content))
        conn.commit()
        return f"'{filename}' uploaded successfully."
    except Exception as e:
        return f"Error uploading: {str(e)}"

def list_pdfs():
    cursor.execute("SELECT filename FROM pdfs ORDER BY id DESC")
    return [row[0] for row in cursor.fetchall()]

def get_pdf_content(filename):
    cursor.execute("SELECT content FROM pdfs WHERE filename = ?", (filename,))
    row = cursor.fetchone()
    return row[0] if row else None
