import os
import json
from modules.voice_engine import speak, listen_command

CONFIG_PATH = "config/user_config.json"

def get_or_set_wake_phrase():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            return data.get("wake_phrase", "hey mesmerizer")

    # First-time setup
    speak("Welcome. Please say your custom wake phrase after the beep.")
    phrase = None
    while not phrase:
        phrase = listen_command()
        if not phrase:
            speak("I didn’t catch that. Try again.")

    # Save wake phrase
    with open(CONFIG_PATH, "w") as f:
        json.dump({"wake_phrase": phrase.lower()}, f)

    speak(f"Got it! I'll respond to '{phrase}' from now on.")
    return phrase.lower()
