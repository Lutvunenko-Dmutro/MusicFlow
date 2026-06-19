import customtkinter as ctk
import pygame
from mutagen.mp3 import MP3
from mutagen import File
try:
    from mutagen.id3 import ID3
except ImportError:
    ID3 = None
from PIL import Image, ImageDraw
import io
import os
import tkinter as tk
from ui.audio_visualizer import  AudioVisualizer

class PlayerBarFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=("#F9FAFB", "#111111"), **kwargs)
        self.app = app
        from core.playback_engine import PlaybackEngine
        self.engine = PlaybackEngine()

        self.shuffle_enabled = False
        self.repeat_mode = 0 # 0=off, 1=all, 2=one

        # Load premium icons
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
        def load_icon(name, size):
            path = os.path.join(icons_dir, name)
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
            return None

        self.icon_play = load_icon("play.png", 22)
        self.icon_pause = load_icon("pause.png", 22)
        self.icon_next = load_icon("next.png", 20)
        self.icon_prev = load_icon("prev.png", 20)
        self.icon_stop = load_icon("stop.png", 18)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        # ── TOP SEPARATOR LINE ───────────────────────────────────────────
        sep = ctk.CTkFrame(self, fg_color=("#E5E7EB", "#2a2a2a"), height=1)
        sep.place(x=0, y=0, relwidth=1)

        # ══════════════════════════════════════════════════════════════════
        # LEFT PANEL — album art + track info + visualizer
        # ══════════════════════════════════════════════════════════════════
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=12)

        # Album art with rounded corners via a canvas trick
        placeholder_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "music_placeholder.png"
        )
        self.default_cover = Image.open(placeholder_path) if os.path.exists(placeholder_path) else None

        self.cover_lbl = ctk.CTkLabel(
            self.info_frame, text="♪", width=56, height=56,
            fg_color=("#E5E7EB", "#222222"), corner_radius=8,
            font=ctk.CTkFont(size=22), text_color=("#9CA3AF", "#555555")
        )
        self.cover_lbl.pack(side="left", padx=(0, 15))

        # Track info column
        self.text_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.text_frame.pack(side="left")

        self.title_lbl = ctk.CTkLabel(
            self.text_frame, text="No track selected",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=("#111827", "#f1f5f9"), anchor="w", width=160
        )
        self.title_lbl.pack(anchor="w")

        self.artist_lbl = ctk.CTkLabel(
            self.text_frame, text="-",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#6B7280", "#6b7280"), anchor="w", width=160
        )
        self.artist_lbl.pack(anchor="w", pady=(2, 0))

        # Visualizer — positioned after text
        self.visualizer_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.visualizer_frame.pack(side="left", padx=(18, 0))
        self.visualizer = AudioVisualizer(
            self.visualizer_frame,
            app=self.app,
            width=240, height=48, bars=100
        )
        self.visualizer.pack()

        # ══════════════════════════════════════════════════════════════════
        # CENTER PANEL — play controls + progress bar
        # ══════════════════════════════════════════════════════════════════
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=1, column=1, pady=12)

        self.controls_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.controls_frame.pack(pady=(12, 5))

        btn_cfg = dict(text="", fg_color="transparent", hover_color=("#E5E7EB", "#1e1e1e"), corner_radius=20)
        btn_text_cfg = dict(fg_color="transparent", hover_color=("#E5E7EB", "#1e1e1e"), corner_radius=20, font=ctk.CTkFont(size=18), text_color=("#6B7280", "#9ca3af"))

        self.btn_shuffle = ctk.CTkButton(
            self.controls_frame, text="🔀", width=40, height=40,
            command=self.toggle_shuffle, **btn_text_cfg
        )
        self.btn_shuffle.pack(side="left", padx=(0, 4))

        self.btn_prev = ctk.CTkButton(
            self.controls_frame, image=self.icon_prev, width=40, height=40,
            command=lambda: self.app.play_prev_song(), **btn_cfg
        )
        self.btn_prev.pack(side="left", padx=(0, 8))

        self.btn_play_pause = ctk.CTkButton(
            self.controls_frame, text="", image=self.icon_play,
            width=50, height=50, corner_radius=25,
            fg_color="#E52D27", hover_color="#c0241f",
            command=self.toggle_play
        )
        self.btn_play_pause.pack(side="left", padx=10)

        self.btn_next = ctk.CTkButton(
            self.controls_frame, image=self.icon_next, width=40, height=40,
            command=lambda: self.app.play_next_song(), **btn_cfg
        )
        self.btn_next.pack(side="left", padx=(8, 0))

        self.btn_stop = ctk.CTkButton(
            self.controls_frame, image=self.icon_stop, width=40, height=40,
            command=self.stop_music, **btn_cfg
        )
        self.btn_stop.pack(side="left", padx=(8, 4))

        self.btn_repeat = ctk.CTkButton(
            self.controls_frame, text="🔁", width=40, height=40,
            command=self.toggle_repeat, **btn_text_cfg
        )
        self.btn_repeat.pack(side="left", padx=(0, 0))

        # Progress Bar & Times
        self.progress_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=40)

        self.time_current_lbl = ctk.CTkLabel(
            self.progress_frame, text="0:00",
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#6b7280"), width=35
        )
        self.time_current_lbl.pack(side="left", padx=10)

        self.progress_slider = ctk.CTkSlider(
            self.progress_frame, from_=0, to=100,
            command=self.seek,
            button_color=("#111827", "#ffffff"),
            button_hover_color=("#374151", "#f9fafb"),
            fg_color=("#D1D5DB", "#333333"),
            progress_color="#E52D27",
            height=12
        )
        self.progress_slider.set(0)
        self.progress_slider.pack(side="left", padx=8)

        self.time_total_lbl = ctk.CTkLabel(
            self.progress_frame, text="0:00",
            font=ctk.CTkFont(size=12),
            text_color=("#6B7280", "#6b7280"), width=35
        )
        self.time_total_lbl.pack(side="right", padx=10)

        # ══════════════════════════════════════════════════════════════════
        # RIGHT PANEL — volume
        # ══════════════════════════════════════════════════════════════════
        self.volume_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.volume_frame.grid(row=1, column=2, sticky="e", padx=(10, 24), pady=12)

        self.btn_lyrics = ctk.CTkButton(
            self.volume_frame, text="💬", width=30, height=30,
            fg_color="transparent", hover_color=("#E5E7EB", "#1e1e1e"),
            font=ctk.CTkFont(size=16), text_color=("#6B7280", "#6b7280"),
            command=self.show_lyrics
        )
        self.btn_lyrics.pack(side="left", padx=(0, 10))

        self.vol_icon_lbl = ctk.CTkLabel(
            self.volume_frame, text="🔉",
            font=ctk.CTkFont(size=14), text_color=("#6B7280", "#6b7280")
        )
        self.vol_icon_lbl.pack(side="left", padx=5)

        self.volume_slider = ctk.CTkSlider(
            self.volume_frame, from_=0, to=1,
            width=100, height=12,
            button_color=("#6B7280", "#9ca3af"),
            button_hover_color=("#374151", "#f3f4f6"),
            fg_color=("#D1D5DB", "#2a2a2a"),
            progress_color="#E52D27",
            command=self.set_volume
        )
        self.volume_slider.set(0.5)
        self.volume_slider.pack(side="left")
        self.engine.set_volume(0.5)

        # ══════════════════════════════════════════════════════════════════
        # MINI KARAOKE LYRICS (Center overlay)
        # ══════════════════════════════════════════════════════════════════
        self.mini_lyrics_lbl = ctk.CTkLabel(
            self.volume_frame, text=" ", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FCA5A5", # Light red/salmon color
            width=180, anchor="e"
        )
        self.mini_lyrics_lbl.pack(side="left", padx=(0, 20), before=self.btn_lyrics)
        
        self.current_lyrics_lines = []

        # Адаптивний дизайн (Media Queries)
        self.bind("<Configure>", self.on_resize)

        self.update_progress_loop()

    def on_resize(self, event):
        # Відслідковуємо зміну розміру тільки самої панелі плеєра
        if event.widget == self:
            width = event.width
            
            # Якщо вікно менше 900px, ховаємо текст караоке
            if width < 900:
                if self.mini_lyrics_lbl.winfo_ismapped():
                    self.mini_lyrics_lbl.pack_forget()
            else:
                if not self.mini_lyrics_lbl.winfo_ismapped():
                    self.mini_lyrics_lbl.pack(side="left", padx=(0, 20), before=self.btn_lyrics)
                    
            # Якщо вікно менше 700px, ховаємо візуалізатор
            if width < 700:
                if self.visualizer_frame.winfo_ismapped():
                    self.visualizer_frame.pack_forget()
            else:
                if not self.visualizer_frame.winfo_ismapped():
                    self.visualizer_frame.pack(side="left", padx=(18, 0))

    # ─────────────────────────────────────────────────────────────────────
    def load_and_play(self, path):
        if not os.path.exists(path): return

        self.current_song_path = path
        self.current_lyrics_lines = []
        if hasattr(self, 'mini_lyrics_lbl'):
            self.mini_lyrics_lbl.configure(text="")
            
        if not self.engine.load_song(path):
            return
            
        self.current_lyrics_lines = []
        if hasattr(self, 'mini_lyrics_lbl'):
            self.mini_lyrics_lbl.configure(text="")
            
        try:
            self.visualizer.load_song(path)
            self.engine.play()
            
            self.btn_play_pause.configure(image=self.icon_pause)
            self.visualizer.start()

            self.time_total_lbl.configure(text=self.format_time(self.engine.song_length))
            from utils.metadata_utils import extract_track_metadata, parse_lrc_text
            
            metadata = extract_track_metadata(path)
            title = metadata.get('title')
            artist = metadata.get('artist')
            cover_img = metadata.get('cover_img')
            
            lyrics_text = metadata.get('lyrics_text')
            if lyrics_text:
                self.current_lyrics_lines = parse_lrc_text(lyrics_text)

            if cover_img is None and self.default_cover is not None:
                cover_img = self.default_cover.copy()

            if cover_img:
                w, h = cover_img.size
                sz = min(w, h)
                cover_img = cover_img.crop(((w-sz)//2, (h-sz)//2, (w+sz)//2, (h+sz)//2))
                cover_img = cover_img.resize((48, 48), Image.LANCZOS)
                photo = ctk.CTkImage(light_image=cover_img, dark_image=cover_img, size=(48, 48))
                self.photo = photo  # keep reference
                self.cover_lbl.configure(image=photo, text="")

            filename = os.path.basename(path)
            display_title = title if title else (filename[:28]+"…" if len(filename) > 28 else filename)
            display_artist = artist if artist else "Playing from library"

            self.title_lbl.configure(text=display_title)
            self.artist_lbl.configure(text=display_artist)

            # Додаємо або оновлюємо історію прослуховування
            try:
                from core.history_manager import add_to_json_history
                # Оскільки у нас може не бути прямого URL для локального файлу, передаємо порожній рядок
                add_to_json_history(display_title, display_artist, "", path)
                
                # Якщо вкладка History відкрита прямо зараз, оновлюємо її
                if hasattr(self.app, 'history_area') and self.app.history_area.winfo_manager():
                    self.app.history_area.load_history()
            except Exception as e:
                print(f"Failed to update history: {e}")

        except Exception as e:
            print(f"Error playing {path}: {e}")

    def toggle_play(self):
        if not self.engine.current_song_path: return

        if self.engine.is_playing:
            self.engine.pause()
            self.btn_play_pause.configure(image=self.icon_play)
        else:
            self.engine.play()
            self.btn_play_pause.configure(image=self.icon_pause)

    def play_specific_music(self, file_path):
        self.load_and_play(file_path)

    def stop_music(self):
        self.engine.pause()
        self.engine.current_pos = 0.0
        self.engine.is_playing = False
        self.btn_play_pause.configure(image=self.icon_play)
        self.progress_slider.set(0)
        self.time_current_lbl.configure(text="0:00")
        if hasattr(self, 'visualizer'):
            self.visualizer.stop()

    def seek(self, value):
        if not self.engine.current_song_path: return
        pos = (float(value) / 100) * self.engine.song_length
        self.engine.seek(pos)

    def set_volume(self, value):
        self.engine.set_volume(value)

    def toggle_shuffle(self):
        self.shuffle_enabled = not self.shuffle_enabled
        if self.shuffle_enabled:
            self.btn_shuffle.configure(text_color="#E52D27")
        else:
            self.btn_shuffle.configure(text_color=("#6B7280", "#9ca3af"))

    def toggle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3
        if self.repeat_mode == 0:
            self.btn_repeat.configure(text="🔁", text_color=("#6B7280", "#9ca3af"))
        elif self.repeat_mode == 1:
            self.btn_repeat.configure(text="🔁", text_color="#E52D27")
        elif self.repeat_mode == 2:
            self.btn_repeat.configure(text="🔂", text_color="#E52D27")

    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

    def show_lyrics(self):
        if not self.current_song_path: return
        lyrics = None
        try:
            from mutagen.id3 import ID3
            if ID3 is not None:
                tags = ID3(self.current_song_path)
                for key, tag in tags.items():
                    if key.startswith('USLT'):
                        lyrics = tag.text
                        break
        except Exception:
            pass

        self._display_lyrics_window(lyrics)

    def _ask_install_model(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("ШІ Модель відсутня")
        dialog.geometry("420x180")
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = self.app.winfo_x() + (self.app.winfo_width() - 420) // 2
        y = self.app.winfo_y() + (self.app.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")
        
        lbl = ctk.CTkLabel(dialog, text="Для генерації тексту пісень потрібна AI модель.\nБажаєте завантажити її зараз (~250 МБ)?\nЦе потрібно зробити лише один раз.", font=ctk.CTkFont(size=14))
        lbl.pack(pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        def on_yes():
            dialog.destroy()
            from core.ai_lyrics import download_ai_model_ui, transcribe_audio_ui
            download_ai_model_ui(self.app, on_complete=lambda: transcribe_audio_ui(self.app, self.current_song_path, on_success=self._display_lyrics_window))
            
        btn_yes = ctk.CTkButton(btn_frame, text="Так, завантажити", fg_color="#E52D27", hover_color="#c0241f", command=on_yes)
        btn_yes.pack(side="left", expand=True, padx=10)
        
        btn_no = ctk.CTkButton(btn_frame, text="Ні", fg_color=("#D1D5DB", "#333333"), hover_color=("#9CA3AF", "#4b5563"), text_color=("#111827", "#ffffff"), command=dialog.destroy)
        btn_no.pack(side="right", expand=True, padx=10)

    def _display_lyrics_window(self, lyrics):
        from ui.lyrics_karaoke import KaraokeLyricsUI
        
        def on_generate():
            from core.ai_lyrics import is_model_installed, transcribe_audio_ui
            if not is_model_installed():
                self._ask_install_model()
            else:
                transcribe_audio_ui(self.app, self.current_song_path, on_success=self._display_lyrics_window)
                
        self.lyrics_ui = KaraokeLyricsUI(self.app, lyrics, on_regenerate=on_generate)

    def update_progress_loop(self):
        if self.engine.is_playing:
            actual_pos = self.engine.get_actual_pos()
            if self.engine.song_length > 0:
                percent = (actual_pos / self.engine.song_length) * 100
                if percent <= 100:
                    self.progress_slider.set(percent)
                    self.time_current_lbl.configure(text=self.format_time(actual_pos))
                    
                    if hasattr(self, 'lyrics_ui') and getattr(self.lyrics_ui, 'dialog', None) and self.lyrics_ui.dialog.winfo_exists():
                        self.lyrics_ui.sync_lyrics(actual_pos)
                        
                    # Оновлення тексту караоке
                    if hasattr(self, 'current_lyrics_lines') and self.current_lyrics_lines and hasattr(self, 'mini_lyrics_lbl'):
                        current_line = ""
                        for item in self.current_lyrics_lines:
                            if actual_pos >= item[0]:
                                current_line = item[1]
                        if current_line:
                            # Адаптивне обрізання тексту в залежності від ширини вікна
                            window_width = self.winfo_width()
                            max_chars = 40 # За замовчуванням
                            
                            if window_width < 1100:
                                max_chars = 30
                            if window_width < 1000:
                                max_chars = 20
                            if window_width < 950:
                                max_chars = 12
                                
                            if len(current_line) > max_chars:
                                current_line = current_line[:max_chars] + "..."
                                
                            self.mini_lyrics_lbl.configure(text=current_line)
                        else:
                            self.mini_lyrics_lbl.configure(text="")
                    else:
                        if hasattr(self, 'mini_lyrics_lbl'):
                            self.mini_lyrics_lbl.configure(text="")
                    
                    if percent >= 99.8:
                        if self.repeat_mode == 2:
                            self.seek(0)
                        else:
                            self.stop_music()
                            self.progress_slider.set(100)
                            # Авто-наступна пісня (Playlist Manager handle it?)
                            if hasattr(self.app, 'play_next_song'):
                                self.app.after(500, self.app.play_next_song)

        self.after(500, self.update_progress_loop)
