import os
import urllib.request
import subprocess
import time

def get_ytdlp_path():
    app_data = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), "YouTubeMusicPro", "bin")
    if not os.path.exists(app_data):
        os.makedirs(app_data, exist_ok=True)
    return os.path.join(app_data, "yt-dlp.exe")

def ensure_ytdlp_exists(status_callback=None):
    exe_path = get_ytdlp_path()
    if not os.path.exists(exe_path):
        if status_callback:
            status_callback("⬇️ Завантаження yt-dlp.exe (одноразово)...")
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        urllib.request.urlretrieve(url, exe_path)
    return exe_path

def update_ytdlp(status_callback=None, force=False):
    exe_path = get_ytdlp_path()
    if os.path.exists(exe_path):
        app_data = os.path.dirname(exe_path)
        last_update_file = os.path.join(app_data, "last_update.txt")
        
        # Перевіряємо чи пройшло 24 години (86400 секунд)
        if not force and os.path.exists(last_update_file):
            with open(last_update_file, "r") as f:
                try:
                    last_check = float(f.read().strip())
                    if time.time() - last_check < 86400:
                        return # Ще зарано перевіряти оновлення
                except Exception:
                    pass

        if status_callback:
            status_callback("Перевірка оновлень yt-dlp.exe...")
        try:
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            subprocess.run([exe_path, "-U"], creationflags=creationflags)
            
            # Записуємо час останньої перевірки
            with open(last_update_file, "w") as f:
                f.write(str(time.time()))
        except Exception:
            pass
