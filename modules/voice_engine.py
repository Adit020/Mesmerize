import pyttsx3
import speech_recognition as sr

# ---------- TTS SETUP ----------
engine = pyttsx3.init()
engine.setProperty('rate', 170)  # adjust speed if needed
engine.setProperty('voice', engine.getProperty('voices')[0].id)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# ---------- STT FUNCTION ----------
def listen_command(timeout=7):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.2)
        try:
            audio = recognizer.listen(source, timeout=timeout)
            query = recognizer.recognize_google(audio, language="en-in")
            return query.lower()
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand that.")
        except sr.RequestError:
            speak("Network error occurred.")
    return None
