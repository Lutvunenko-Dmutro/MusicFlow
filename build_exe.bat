@echo off
echo ==============================================
echo Building YT Music Downloader (EXE Compilation)
echo ==============================================

echo 1. Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
del /s /q *.spec 2>nul

echo 2. Installing requirements...
python -m pip install -r requirements.txt
python -m pip install pyinstaller customtkinter static_ffmpeg pillow pygame

echo 3. Compiling to EXE...
python -m PyInstaller --noconfirm --clean --onedir --windowed --icon "icon.ico" --name "YT_Music_Downloader" --add-data "icons;icons" --collect-all customtkinter --collect-all static_ffmpeg gui_app.py

echo ==============================================
echo Done! Your app is in the "dist\YT_Music_Downloader" folder.
echo You can create a shortcut to YT_Music_Downloader.exe to your Desktop!
echo ==============================================
pause
