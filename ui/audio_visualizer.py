import tkinter as tk
import threading
import subprocess
import numpy as np
import hashlib
import os
import json

# --- Constants ---
SAMPLE_RATE = 44100
FFT_SIZE    = 8192          # larger = finer frequency resolution (5.38 Hz/bin vs 10.77)
# Per-Band AGC (leaky integrator) — adapts to any music loudness automatically
AGC_ALPHA   = 0.02
AGC_MIN     = 1e-6
ATTACK      = 0.90
RELEASE     = 0.22
GRAVITY     = 0.9

class AudioVisualizer(tk.Canvas):
    def __init__(self, master, app=None, bg_color="#181818", fg_color="#E52D27",
                 width=200, height=35, bars=80, **kwargs):
        self.app = app
        self.bg_color  = bg_color
        self._current_bg = self._get_theme_bg(self.bg_color)
        super().__init__(master, bg=self._current_bg, width=width, height=height,
                         highlightthickness=0, **kwargs)
        self.bars      = bars
        self.bar_w     = 2
        self.spacing   = 1
        self.H         = height          # canvas height
        self.FLOOR     = height - 2      # baseline y-coordinate

        # bar state  (0.0 – 1.0 normalised height)
        self._bar_h    = np.zeros(bars, dtype=np.float32)
        # peak-dot state
        self._dot_y    = np.full(bars, float(self.FLOOR), dtype=np.float32)
        self._dot_v    = np.zeros(bars, dtype=np.float32)

        self._lines    = []
        self._dots     = []
        self._audio_frames = []
        self._fps      = 30
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

    # ------------------------------------------------------------------ colours
    def _bar_color(self, i):
        """Red → Orange → Gold gradient."""
        t = i / max(1, self.bars - 1)
        r = int(229 + (255 - 229) * t)
        g = int(45  + (183 - 45)  * t)
        b = int(39  + (3   - 39)  * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ------------------------------------------------------------------ layout
    def _build_bars(self):
        self.delete("all")
        self._lines.clear()
        self._dots.clear()

        W = self.winfo_width()
        if W < 10:
            W = int(self["width"])

        total_w = self.bars * (self.bar_w + self.spacing) - self.spacing
        ox = (W - total_w) // 2

        for i in range(self.bars):
            x = ox + i * (self.bar_w + self.spacing) + self.bar_w // 2
            color = self._bar_color(i)
            line = self.create_line(x, self.FLOOR, x, self.FLOOR,
                                    fill=color, width=self.bar_w,
                                    capstyle=tk.ROUND, state="hidden" if not self._is_playing else "normal")
            dot = self.create_line(x, self.FLOOR, x, self.FLOOR,
                                   fill="#39FF14", width=self.bar_w,
                                   capstyle=tk.ROUND, state="hidden" if not self._is_playing else "normal")
            self._lines.append(line)
            self._dots.append(dot)

        self._bar_h[:] = 0.0
        self._dot_y[:] = self.FLOOR
        self._dot_v[:] = 0.0

    # ------------------------------------------------------------------ FFT loader
    def _cache_path(self, filepath):
        """Unique cache file path per song + current settings."""
        music_dir = os.path.dirname(os.path.abspath(filepath))
        cache_dir = os.path.join(music_dir, ".viz_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache key: file path + size + FFT settings
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        raw_key = f"{filepath}|{file_size}|{FFT_SIZE}|{self.bars}"
        key_hash = hashlib.md5(raw_key.encode()).hexdigest()
        return os.path.join(cache_dir, f"{key_hash}.npy")

    def load_song(self, filepath):
        """Load pre-computed frames from cache or compute them in a background thread."""
        self._audio_frames = []
        
        def _worker():
            # --- Try loading from cache first ---
            cache_file = self._cache_path(filepath)
            if os.path.exists(cache_file):
                try:
                    cached = np.load(cache_file, allow_pickle=False)
                    self._audio_frames = cached.tolist()
                    print(f"[Visualizer] ⚡ Cache hit: {os.path.basename(filepath)}")
                    return
                except Exception as e:
                    print(f"[Visualizer] Cache read failed, recomputing: {e}")

            # --- Cache miss: full FFT analysis ---
            print(f"[Visualizer] 🔍 Analysing: {os.path.basename(filepath)}")
            try:
                try:
                    import static_ffmpeg
                    ffmpeg = static_ffmpeg.get_ffmpeg_exe()
                except Exception:
                    ffmpeg = "ffmpeg"

                cmd = [ffmpeg, "-i", filepath, "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-loglevel", "quiet", "-"]
                
                # Helper to get spectrum data
                def get_spectrum_data():
                    import os
                    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
                    chunk = SAMPLE_RATE // self._fps
                    buf = np.zeros(FFT_SIZE, dtype=np.float32)
                    win = np.hanning(FFT_SIZE).astype(np.float32)
                    hz_per_bin = SAMPLE_RATE / FFT_SIZE
                    lo_bin = max(1, int(20 / hz_per_bin))
                    hi_bin = min(FFT_SIZE // 2, int(16000 / hz_per_bin))
                    edges = np.logspace(np.log10(lo_bin), np.log10(hi_bin), self.bars + 1, dtype=int)
                    
                    data_list = []
                    while True:
                        raw = proc.stdout.read(chunk * 2)
                        if len(raw) < chunk * 2: break
                        new_s = (np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0)
                        buf = np.roll(buf, -chunk)
                        buf[-chunk:] = new_s
                        spec = np.abs(np.fft.rfft(buf * win)) / FFT_SIZE
                        bands = [float(np.sqrt(np.mean(spec[edges[k]:max(edges[k]+1, edges[k+1])]**2))) for k in range(self.bars)]
                        data_list.append(bands)
                    return np.array(data_list)

                raw_data = get_spectrum_data()
                
                # Pass 1: compute per-band 95th percentile energy as AGC reference
                # p95 means: only the loudest 5% of moments will push bars near the top
                agc_p95 = np.array([
                    max(AGC_MIN, float(np.percentile(raw_data[:, k], 95)))
                    if len(raw_data) > 0 else AGC_MIN
                    for k in range(self.bars)
                ], dtype=np.float64)
                
                # Pass 2: Generate frames using p95 as ceiling reference
                # tanh(1.0 * 0.85) = 0.69 at p95 level → bars sit at ~69% height normally
                # Only extreme transients briefly touch ~85-90%
                agc_curr = agc_p95.copy()
                for bands in raw_data:
                    frame = []
                    for k in range(self.bars):
                        normalized = bands[k] / agc_curr[k]
                        val = float(np.tanh(normalized * 0.85))
                        frame.append(val)
                        # Slowly adapt to long-term changes in volume
                        agc_curr[k] = AGC_ALPHA * max(bands[k], AGC_MIN) + (1 - AGC_ALPHA) * agc_curr[k]
                    self._audio_frames.append(frame)

                # Save to cache for instant load next time
                if self._audio_frames:
                    try:
                        np.save(cache_file, np.array(self._audio_frames, dtype=np.float32))
                        print(f"[Visualizer] 💾 Cached: {os.path.basename(filepath)}")
                    except Exception as e:
                        print(f"[Visualizer] Cache write failed: {e}")

            except Exception as exc:
                print(f"[Visualizer FFT error] {exc}")

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------ playback control
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

    # ------------------------------------------------------------------ animation loop
    def _tick(self):
        if not self._is_playing:
            return

        try:
            import pygame
            if pygame.mixer.music.get_busy():
                pos_ms = pygame.mixer.music.get_pos()
                frame_idx = int(pos_ms / 1000.0 * self._fps)

                if 0 <= frame_idx < len(self._audio_frames):
                    targets = self._audio_frames[frame_idx]
                    self._update_bars(targets)
                # else: keep bars at current position until data arrives
        except Exception:
            pass

        self.after(int(1000 / self._fps), self._tick)

    def _update_bars(self, targets):
        usable_h = self.FLOOR - 2    # max drawable bar height

        for i, (line, dot) in enumerate(zip(self._lines, self._dots)):
            t = targets[i] if i < len(targets) else 0.0

            # Asymmetric smoothing: fast attack, slow release
            if t > self._bar_h[i]:
                self._bar_h[i] += ATTACK  * (t - self._bar_h[i])
            else:
                self._bar_h[i] += RELEASE * (t - self._bar_h[i])

            h = max(2, self._bar_h[i] * usable_h)
            bar_top = self.FLOOR - h

            # Draw bar
            cx = self.coords(line)
            if cx:
                self.coords(line, cx[0], bar_top, cx[2], self.FLOOR)

                # Peak dot physics
                if bar_top <= self._dot_y[i]:
                    self._dot_y[i] = bar_top
                    self._dot_v[i] = -1.5          # upward kick
                else:
                    self._dot_v[i] += GRAVITY
                    self._dot_y[i] += self._dot_v[i]
                    if self._dot_y[i] > self.FLOOR:
                        self._dot_y[i] = self.FLOOR
                        self._dot_v[i] = 0.0

                dy = self._dot_y[i]
                self.coords(dot, cx[0], dy - 3, cx[2], dy)

    # ------------------------------------------------------------------ settle (stop animation)
    def _get_theme_bg(self, fallback):
        if self.app:
            try:
                # Get actual applied mode from CTk
                mode = self.app._get_appearance_mode().lower()
                return "#F9FAFB" if mode == "light" else "#111111"
            except Exception:
                pass
        return fallback

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
