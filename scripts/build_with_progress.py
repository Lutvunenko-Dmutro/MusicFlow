import os
import sys
import subprocess
import shutil
import time

def clear_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()

def main():
    os.system('color') # Enable ANSI colors in Windows CMD
    print("\033[1;36m==============================================\033[0m")
    print("\033[1;37m Building Music Flow (EXE Compilation)\033[0m")
    print("\033[1;36m==============================================\033[0m\n")

    # 1. Clean only dist, keep build for caching
    print("\033[1;33m[1/3] Preparing build environment...\033[0m")
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    # 2. Install reqs
    if "--skip-install" in sys.argv:
        print("\033[1;33m[2/3] Skipping pip install (Fast mode)...\033[0m")
    else:
        print("\033[1;33m[2/3] Installing requirements...\033[0m")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyinstaller", "customtkinter", "static_ffmpeg", "pillow", "pygame"])

    # 3. Compile
    print("\033[1;33m[3/3] Compiling to EXE (this takes 1-2 minutes)...\033[0m")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onedir", "--windowed",
        "--icon", "icon.ico", "--name", "YT_Music_Downloader",
        "--add-data", "icons;icons", "--add-data", "locales;locales", "--add-data", "icon.ico;.",
        "--collect-all", "customtkinter", "--collect-all", "static_ffmpeg",
        "--collect-all", "librosa", "--collect-all", "scipy", "--collect-all", "numba", "--collect-all", "llvmlite",
        "--exclude-module", "PyQt6", "--exclude-module", "PySide6",
        "--exclude-module", "PyQt5", "--exclude-module", "matplotlib",
        "--exclude-module", "IPython", "--exclude-module", "torch",
        "--exclude-module", "torchvision", "--exclude-module", "cv2",
        "--exclude-module", "pandas", "--exclude-module", "pyarrow",
        "--exclude-module", "tensorflow", "--exclude-module", "keras",
        "--exclude-module", "tf_keras", "--exclude-module", "tensorboard", "main.py"
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    
    # Progress spinner and bar
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    bar_width = 30
    lines_count = 0
    estimated_total = 700 # Approximate lines of output for this project
    
    for line in process.stdout:
        lines_count += 1
        
        # Calculate fake progress
        progress = min(int((lines_count / estimated_total) * bar_width), bar_width)
        bar = "█" * progress + "░" * (bar_width - progress)
        percent = min(int((lines_count / estimated_total) * 100), 99) # Stop at 99% until fully done
        
        spin_char = spinner[lines_count % len(spinner)]
        
        sys.stdout.write(f"\r\033[1;32m{spin_char} Progress:\033[0m [{bar}] {percent}% ")
        sys.stdout.flush()
        
        if "WARNING" in line or "ERROR" in line:
            # Clear line to print warning nicely, without leaving duplicate progress bars
            sys.stdout.write("\r\033[K")
            color = "\033[1;31m" if "ERROR" in line else "\033[1;33m"
            sys.stdout.write(color + line.strip() + "\033[0m\n")
            
    process.wait()
    
    # Finish 100%
    bar = "█" * bar_width
    sys.stdout.write(f"\r\033[1;32m✔ Progress:\033[0m [{bar}] 100% \n")
    sys.stdout.flush()

    print("\n\033[1;36m==============================================\033[0m")
    if process.returncode == 0:
        print('\033[1;32m✨ Done! Your app is in the "dist\\YT_Music_Downloader" folder.\033[0m')
    else:
        print('\033[1;31m❌ Build failed! Please check errors above.\033[0m')
    print("\033[1;36m==============================================\033[0m")

if __name__ == "__main__":
    main()
