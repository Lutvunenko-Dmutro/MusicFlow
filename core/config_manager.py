import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "output_folder": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "My_Music"),
    "theme": "Dark",
    "quality": "320",
    "embed_lyrics": True,
    "use_sponsorblock": True
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
