*Read this in other languages: [Українська](README.uk.md)*

# 🎵 Music Flow
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-blueviolet?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Music Flow** is a modern, fast, and feature-rich desktop application for downloading and listening to music directly from YouTube and YouTube Music. Built with Python, it features a beautiful graphical user interface, an embedded music player with a real-time audio visualizer, a smart local library manager, and robust multi-language support.

---

## ✨ Key Features

- **🚀 Direct Downloads (Tracks & Playlists)**: Just paste a link to a YouTube video, track, or a full playlist. The app will automatically detect the type and download the highest quality audio using the embedded `yt-dlp` engine.
- **🎧 Built-in Music Player**: No need for third-party media players. Listen to your downloaded tracks instantly within the app, powered by `pygame`.
- **🎛️ Real-Time Audio Visualizer**: Watch your music come to life! An incredible, buttery-smooth visualizer reacts to the frequencies (FFT) of the currently playing track.
- **🖼️ Smart Metadata & Covers**: The app automatically fetches video thumbnails, artist names, track titles, and embeds them into the MP3 metadata (ID3 tags) along with lyrics.
- **🚫 SponsorBlock Integration**: Automatically skips or removes non-music segments (intros, outros, sponsorships) from downloaded tracks to keep your music pure.
- **🎨 Beautiful Theme System**: Full support for **Dark**, **Light**, and **System** themes. The UI dynamically adapts to your OS preferences.
- **🌍 Multi-language Support**: Interface is fully localized in **English** and **Ukrainian**, easily extensible via JSON files.
- **📚 SQLite Library & History**: Manage all your downloaded music efficiently. Play, delete, or browse your local library in one click with a fast SQLite backend.
- **⚡ Multi-threading**: The UI never freezes. Downloading, audio processing, and metadata gathering all happen flawlessly in the background.

---

## 📸 Tech Stack

- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)**: Powers the modern and responsive GUI.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**: Reliable, lightning-fast core for extracting audio from YouTube.
- **[Pygame](https://www.pygame.org/)**: Ensures smooth audio playback with minimal latency.
- **[NumPy](https://numpy.org/)**: Performs fast mathematical computations (Fast Fourier Transform) for the audio visualizer.
- **[Pillow](https://python-pillow.org/)**: Image processing for high-quality track covers and UI icons.
- **[FFmpeg](https://ffmpeg.org/)**: Audio conversion, metadata embedding, and spectrum analysis.
- **SQLite**: Local database for instant loading of your music library and history.

---

## 🚀 Getting Started

### 📥 Method 1: Pre-built Executable (.exe) - Easiest!
You don't need Python or any coding knowledge.
1. Go to the **[Releases](../../releases)** page on the right sidebar.
2. Download the latest `MusicFlow.exe`.
3. Double-click and enjoy!

### 🛠️ Method 2: Run from Source (For Developers)

If you want to run the app directly from Python or modify the code:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/MusicFlow.git
   cd MusicFlow
   ```

2. **Install dependencies:**
   Make sure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

### 📦 Method 3: Build a Standalone Executable Yourself

Want to share the app with friends who don't have Python installed? You can build a fully portable Windows `.exe` file!

Just double-click this batch script:
```bash
build_exe.bat
```
*(This script will automatically clear the old cache, install dependencies into a virtual environment, and package the app using PyInstaller).*

Once the build is complete, your ready-to-use application will be located in the `dist/Music_Flow/` folder!

---

## 📂 Project Structure

```text
📦 MusicFlow
 ┣ 📂 core/                    # Core logic (download engine, player, history, API clients)
 ┣ 📂 ui/                      # Graphical interface components (CustomTkinter widgets)
 ┣ 📂 utils/                   # Helper functions (API parsing, regex)
 ┣ 📂 locales/                 # Translation JSON files (en, uk)
 ┣ 📂 icons/                   # App icons and UI assets
 ┣ 📜 main.py                  # Main entry point of the application
 ┣ 📜 build_exe.bat            # Script for automated .exe compilation
 ┣ 📜 requirements.txt         # Python dependencies
 ┗ 📜 ...
```

---

## 🤝 Contributing

Feedback, suggestions, and ideas for new features are always welcome!
If you know how to make the app even better — feel free to fork the repository and submit a Pull Request.

## 📝 License

This project is created exclusively for educational and personal purposes. Music downloaded using this tool should be used in accordance with YouTube's Terms of Service and your local copyright laws. Distributed under the MIT License.
