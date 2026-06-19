import os
import shutil
import subprocess

def clean_old_builds():
    print("Очищення старих файлів збірки...")
    
    # Видалення папок build та dist
    dirs_to_remove = ["build", "dist"]
    for d in dirs_to_remove:
        if os.path.exists(d):
            print(f"Видалення папки {d}...")
            shutil.rmtree(d)
            
    # Видалення старих .spec файлів
    for f in os.listdir("."):
        if f.endswith(".spec"):
            print(f"Видалення файлу {f}...")
            os.remove(f)

def build_exe():
    print("\nЗапуск PyInstaller...")
    cmd = [
        "python", "-m", "PyInstaller",
        "--noconfirm",           # Не питати підтвердження при перезаписі
        "--clean",               # Очищення кешу PyInstaller
        "--onedir",              # Зібрати в одну папку (швидше працює)
        "--windowed",            # Без консольного вікна
        "--name", "YT_Music_Downloader",
        "--icon", "icon.ico",
        "--collect-all", "customtkinter",
        "--collect-all", "static_ffmpeg",
        "gui_app.py"
    ]
    
    # Запускаємо процес
    subprocess.run(cmd)
    print("\n✅ Збірка успішно завершена! Шукайте програму в папці 'dist'.")

if __name__ == "__main__":
    # Переконуємось, що ми в правильній директорії
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    clean_old_builds()
    build_exe()
