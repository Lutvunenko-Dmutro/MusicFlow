import customtkinter as ctk
from core.playback_engine import PlaybackEngine
from ui.player_bar_ui import build_player_bar
import ui.player_bar_logic as logic


class PlayerBarFrame(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=("#F9FAFB", "#111111"), **kwargs)
        self.app = app
        self.engine = PlaybackEngine()

        self.shuffle_enabled    = False
        self.repeat_mode        = 0  # 0=off, 1=all, 2=one
        self.is_seeking         = False
        self.seek_timer         = None
        self.current_song_path  = None
        self.current_lyrics_lines = []

        build_player_bar(self)

    # ── Delegated to logic module ────────────────────────────────────────────
    def load_and_play(self, path):
        logic.load_and_play(self, path)

    def toggle_play(self):
        logic.toggle_play(self)

    def play_specific_music(self, file_path):
        self.load_and_play(file_path)

    def stop_music(self):
        logic.stop_music(self)

    def seek(self, value):
        logic.seek(self, value)

    def perform_seek(self, value):
        logic.perform_seek(self, value)

    def set_volume(self, value):
        self.engine.set_volume(value)

    def toggle_shuffle(self):
        logic.toggle_shuffle(self)

    def toggle_repeat(self):
        logic.toggle_repeat(self)

    def show_lyrics(self):
        logic.show_lyrics(self)

    def _display_lyrics_window(self, lyrics):
        logic.display_lyrics_window(self, lyrics)

    def _ask_install_model(self):
        logic.ask_install_model(self)

    # ── Resize handler ───────────────────────────────────────────────────────
    def on_resize(self, event):
        if event.widget != self:
            return
        width = event.width
        if width < 900:
            if self.mini_lyrics_lbl.winfo_ismapped():
                self.mini_lyrics_lbl.pack_forget()
        else:
            if not self.mini_lyrics_lbl.winfo_ismapped():
                self.mini_lyrics_lbl.pack(side="left", padx=(0, 20), before=self.btn_lyrics)

        if width < 700:
            if self.visualizer_frame.winfo_ismapped():
                self.visualizer_frame.pack_forget()
        else:
            if not self.visualizer_frame.winfo_ismapped():
                self.visualizer_frame.pack(side="left", padx=(18, 0))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def format_time(self, seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

    def _get_lyrics_line(self, actual_pos, window_width):
        """Повертає поточний рядок лірики для заданої позиції."""
        current_line = ""
        for item in self.current_lyrics_lines:
            if actual_pos >= item[0]:
                current_line = item[1]
        if not current_line:
            return ""
        max_chars = 40
        if window_width < 1100: max_chars = 30
        if window_width < 1000: max_chars = 20
        if window_width < 950:  max_chars = 12
        return current_line[:max_chars] + "..." if len(current_line) > max_chars else current_line

    # ── Progress loop ────────────────────────────────────────────────────────
    def update_progress_loop(self):
        if self.engine.is_playing:
            actual_pos = self.engine.get_actual_pos()
            if self.engine.song_length > 0:
                percent = (actual_pos / self.engine.song_length) * 100
                if percent <= 100:
                    if not self.is_seeking:
                        self.progress_slider.set(percent)
                    self.time_current_lbl.configure(text=self.format_time(actual_pos))

                    # Sync karaoke window
                    if (hasattr(self, 'lyrics_ui') and
                            getattr(self.lyrics_ui, 'dialog', None) and
                            self.lyrics_ui.dialog.winfo_exists()):
                        self.lyrics_ui.sync_lyrics(actual_pos)

                    # Mini lyrics bar
                    if hasattr(self, 'mini_lyrics_lbl'):
                        line = self._get_lyrics_line(actual_pos, self.winfo_width()) \
                            if self.current_lyrics_lines else ""
                        self.mini_lyrics_lbl.configure(text=line)

                    # End of track
                    if percent >= 99.8:
                        if self.repeat_mode == 2:
                            self.seek(0)
                        else:
                            self.stop_music()
                            self.progress_slider.set(100)
                            if hasattr(self.app, 'play_next_song'):
                                self.app.after(500, self.app.play_next_song)

        self.after(500, self.update_progress_loop)
