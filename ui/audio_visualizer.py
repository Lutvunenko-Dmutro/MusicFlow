import tkinter as tk
import threading
import numpy as np

from ui.audio_fft import (
    ATTACK, RELEASE, GRAVITY,
    get_cache_path, load_from_cache, save_to_cache, analyze_audio
)


class AudioVisualizer(tk.Canvas):
    def __init__(self, master, app=None, bg_color="#181818", fg_color="#E52D27",
                 width=200, height=35, bars=80, **kwargs):
        self.app = app
        self.bg_color = bg_color
        self._current_bg = self._get_theme_bg(self.bg_color)
        super().__init__(master, bg=self._current_bg, width=width, height=height,
                         highlightthickness=0, **kwargs)
        self.bars  = bars
        self.bar_w = 2
        self.spacing = 1
        self.H     = height
        self.FLOOR = height - 2

        self._bar_h = np.zeros(bars, dtype=np.float32)
        self._dot_y = np.full(bars, float(self.FLOOR), dtype=np.float32)
        self._dot_v = np.zeros(bars, dtype=np.float32)
        self._lines = []
        self._dots  = []
        self._audio_frames = []
        self._fps   = 60
        self._is_playing = False

        self.bind("<Configure>", lambda e: self._build_bars())
        self.after(100, self._build_bars)
        self._theme_loop()

    def _theme_loop(self):
        expected_bg = self._get_theme_bg(self.bg_color)
        if self._current_bg != expected_bg:
            self._current_bg = expected_bg
            self.configure(bg=expected_bg)
        self.after(500, self._theme_loop)

    def _get_theme_bg(self, fallback):
        if self.app:
            try:
                mode = self.app._get_appearance_mode().lower()
                return "#F9FAFB" if mode == "light" else "#111111"
            except Exception:
                pass
        return fallback

    def _build_bars(self):
        self.delete("all")
        self._lines.clear()
        self._dots.clear()

        W = self.winfo_width()
        if W < 10:
            W = 200

        num_blocks = 5
        group_size = self.bars // num_blocks
        block_gap  = 12
        total_w    = self.bars * (self.bar_w + self.spacing) + (num_blocks - 1) * block_gap
        start_x    = max(0, (W - total_w) // 2)

        BLOCK_COLORS = [
            ("#E52D27", "#FF4B4B"),  # Sub-bass: Deep Red
            ("#F59E0B", "#FCD34D"),  # Bass: Orange
            ("#FBBF24", "#FDE68A"),  # Mids: Yellow
            ("#38BDF8", "#7DD3FC"),  # High-mids: Light Blue
            ("#3B82F6", "#93C5FD"),  # Treble: Deep Blue
        ]

        current_x = start_x
        for i in range(self.bars):
            block_index = min(num_blocks - 1, i // group_size)
            bar_color, dot_color = BLOCK_COLORS[block_index]

            if i > 0 and i % group_size == 0 and i < self.bars - 1:
                current_x += block_gap

            hidden = "hidden" if not self._is_playing else "normal"
            line = self.create_line(current_x, self.FLOOR, current_x, self.FLOOR,
                                    fill=bar_color, width=self.bar_w,
                                    capstyle=tk.ROUND, state=hidden)
            dot = self.create_rectangle(current_x - 1, self.FLOOR,
                                        current_x + 1, self.FLOOR + 2,
                                        fill=dot_color, outline="", state=hidden)
            self._lines.append(line)
            self._dots.append(dot)
            current_x += (self.bar_w + self.spacing)

        self._bar_h[:] = 0.0
        self._dot_y[:] = self.FLOOR
        self._dot_v[:] = 0.0

    def load_song(self, filepath):
        """Завантажує кешовані або обраховує фрейми FFT у фоновому потоці."""
        self._audio_frames = []

        def _worker():
            cache_file = get_cache_path(filepath, self.bars)
            frames = load_from_cache(cache_file)
            if frames is not None:
                self._audio_frames = frames
                print(f"[Visualizer] ⚡ Cache hit: {__import__('os').path.basename(filepath)}")
                return

            print(f"[Visualizer] 🔍 Analysing: {__import__('os').path.basename(filepath)}")
            try:
                frames = analyze_audio(filepath, self.bars, self._fps)
                self._audio_frames = frames
                if frames:
                    save_to_cache(cache_file, frames)
                    print(f"[Visualizer] 💾 Cached: {__import__('os').path.basename(filepath)}")
            except Exception as exc:
                print(f"[Visualizer FFT error] {exc}")

        threading.Thread(target=_worker, daemon=True).start()

    def start(self):
        if not self._is_playing:
            self._is_playing = True
            for line, dot in zip(self._lines, self._dots):
                self.itemconfig(line, state="normal")
                self.itemconfig(dot, state="normal")
            self._tick()

    def stop(self):
        self._is_playing = False
        self._settle()

    def _tick(self):
        if not self._is_playing:
            return
        try:
            import pygame
            if pygame.mixer.music.get_busy():
                pos_sec = 0.0
                if self.app and hasattr(self.app, 'player_bar') and self.app.player_bar.engine:
                    pos_sec = self.app.player_bar.engine.get_actual_pos()
                else:
                    pos_sec = pygame.mixer.music.get_pos() / 1000.0
                frame_idx = int(pos_sec * self._fps)
                if 0 <= frame_idx < len(self._audio_frames):
                    self._update_bars(self._audio_frames[frame_idx])
        except Exception:
            pass
        self.after(int(1000 / self._fps), self._tick)

    def _update_bars(self, targets):
        usable_h = self.FLOOR - 2
        for i, (line, dot) in enumerate(zip(self._lines, self._dots)):
            t = targets[i] if i < len(targets) else 0.0
            if t > self._bar_h[i]:
                self._bar_h[i] += ATTACK  * (t - self._bar_h[i])
            else:
                self._bar_h[i] += RELEASE * (t - self._bar_h[i])

            h = max(2, self._bar_h[i] * usable_h)
            bar_top = self.FLOOR - h
            cx = self.coords(line)
            if not cx:
                continue
            self.coords(line, cx[0], bar_top, cx[2], self.FLOOR)
            if bar_top <= self._dot_y[i]:
                self._dot_y[i] = bar_top
                self._dot_v[i] = -0.8
            else:
                self._dot_v[i] += GRAVITY
                self._dot_y[i] += self._dot_v[i]
                if self._dot_y[i] > self.FLOOR:
                    self._dot_y[i] = self.FLOOR
                    self._dot_v[i] = 0.0
            dy = self._dot_y[i]
            self.coords(dot, cx[0], dy - 3, cx[2], dy)

    def _settle(self):
        if self._is_playing:
            return
        moving = False
        for i, (line, dot) in enumerate(zip(self._lines, self._dots)):
            if self._bar_h[i] > 0.005:
                self._bar_h[i] *= 0.7
                h = max(2, self._bar_h[i] * (self.FLOOR - 2))
                bar_top = self.FLOOR - h
                cx = self.coords(line)
                if cx:
                    self.coords(line, cx[0], bar_top, cx[2], self.FLOOR)
                    self._dot_y[i] = bar_top
                    self.coords(dot, cx[0], bar_top - 3, cx[2], bar_top)
                moving = True
            else:
                cx = self.coords(line)
                if cx:
                    self.coords(dot, cx[0], self.FLOOR, cx[2], self.FLOOR)
        if moving:
            self.after(40, self._settle)
        else:
            for line, dot in zip(self._lines, self._dots):
                self.itemconfig(line, state="hidden")
                self.itemconfig(dot, state="hidden")
