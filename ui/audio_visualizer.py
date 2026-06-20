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
ATTACK      = 0.80
RELEASE     = 0.15
GRAVITY     = 0.35

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
        self._fps      = 60  # Ultra smooth 60 FPS
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
        if W < 10: W = 200

        num_blocks = 5
        group_size = self.bars // num_blocks
        block_gap = 12  # Space between the 5 blocks

        total_w = self.bars * (self.bar_w + self.spacing) + (num_blocks - 1) * block_gap
        start_x = max(0, (W - total_w) // 2)

        current_x = start_x
        for i in range(self.bars):
            # Determine which block this bar belongs to (0 to 4)
            block_index = min(num_blocks - 1, i // group_size)
            
            # Colors for the 5 blocks
            if block_index == 0:
                bar_color = "#E52D27"   # Sub-bass: Deep Red
                dot_color = "#FF4B4B"
            elif block_index == 1:
                bar_color = "#F59E0B"   # Bass: Orange
                dot_color = "#FCD34D"
            elif block_index == 2:
                bar_color = "#FBBF24"   # Mids: Yellow
                dot_color = "#FDE68A"
            elif block_index == 3:
                bar_color = "#38BDF8"   # High-mids: Light Blue
                dot_color = "#7DD3FC"
            else:
                bar_color = "#3B82F6"   # Treble: Deep Blue
                dot_color = "#93C5FD"

            # Add gap between blocks
            if i > 0 and i % group_size == 0 and i < self.bars - 1:
                current_x += block_gap

            x = current_x
            
            # Bottom line (the bar itself)
            line = self.create_line(x, self.FLOOR, x, self.FLOOR,
                                    fill=bar_color, width=self.bar_w, capstyle=tk.ROUND, state="hidden" if not self._is_playing else "normal")
            # Peak dot
            dot = self.create_rectangle(x - 1, self.FLOOR, x + 1, self.FLOOR + 2,
                                        fill=dot_color, outline="", state="hidden" if not self._is_playing else "normal")
            self._lines.append(line)
            self._dots.append(dot)
            
            current_x += (self.bar_w + self.spacing)

        self._bar_h[:] = 0.0
        self._dot_y[:] = self.FLOOR
        self._dot_v[:] = 0.0

    # ------------------------------------------------------------------ FFT loader
    def _cache_path(self, filepath):
        """Unique cache file path per song + current settings."""
        music_dir = os.path.dirname(os.path.abspath(filepath))
        cache_dir = os.path.join(music_dir, ".viz_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache key: file path + size + FFT settings + librosa version
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        raw_key = f"{filepath}|{file_size}|LIBROSA_SMART_STEMS_V1|{self.bars}"
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
            # --- Cache miss: full FFT analysis ---
            print(f"[Visualizer] 🔍 Analysing: {os.path.basename(filepath)}")
            try:
                import librosa
                import scipy.signal
                
                # Load audio with librosa
                y, sr = librosa.load(filepath, sr=22050, mono=True)
                
                # ---------------------------------------------------------
                # SMART STEM SEPARATION (AI-like instrument isolation)
                # ---------------------------------------------------------
                # 1. Isolate Percussion (Drums, Kicks, Snares, Cymbals)
                y_perc = librosa.effects.percussive(y, margin=2.0)
                
                # 2. Isolate Harmonics (Vocals, Guitars, Synths)
                y_harm = librosa.effects.harmonic(y, margin=2.0)
                
                # 3. Isolate Pure Bass (< 250 Hz) using a Low-Pass Filter
                def lowpass_filter(data, cutoff, fs, order=5):
                    nyq = 0.5 * fs
                    normal_cutoff = cutoff / nyq
                    b, a = scipy.signal.butter(order, normal_cutoff, btype='low', analog=False)
                    return scipy.signal.lfilter(b, a, data)
                
                y_bass = lowpass_filter(y, cutoff=250.0, fs=sr)
                
                # Calculate hop length to match our FPS
                hop_length = int(sr / self._fps)
                
                # ---------------------------------------------------------
                # GENERATE SPECTROGRAMS FOR EACH INSTRUMENT (12 bars each)
                # ---------------------------------------------------------
                bars_per_block = self.bars // 5  # 12 bars
                
                # Block 0: BASS (Deep, smooth, low frequencies)
                S_bass = librosa.feature.melspectrogram(y=y_bass, sr=sr, n_mels=bars_per_block, fmin=20, fmax=250, hop_length=hop_length)
                
                # Block 1: DRUMS (Punchy, percussive impacts)
                S_drums = librosa.feature.melspectrogram(y=y_perc, sr=sr, n_mels=bars_per_block, fmin=50, fmax=1000, hop_length=hop_length)
                
                # Block 2: VOCALS / GUITAR (Harmonic mid-range)
                S_vocals = librosa.feature.melspectrogram(y=y_harm, sr=sr, n_mels=bars_per_block, fmin=300, fmax=3000, hop_length=hop_length)
                
                # Block 3: SYNTHS / HIGH MELODY (Harmonic high-range)
                S_melody = librosa.feature.melspectrogram(y=y_harm, sr=sr, n_mels=bars_per_block, fmin=1500, fmax=6000, hop_length=hop_length)
                
                # Block 4: CYMBALS / HI-HATS (Percussive high-range)
                S_cymbals = librosa.feature.melspectrogram(y=y_perc, sr=sr, n_mels=bars_per_block, fmin=4000, fmax=10000, hop_length=hop_length)
                
                # Combine them into one 60-bar matrix
                S_combined = np.vstack([S_bass, S_drums, S_vocals, S_melody, S_cymbals])
                
                # Convert power to Decibels (dB)
                S_db = librosa.power_to_db(S_combined, ref=np.max)
                
                # NORMALIZATION:
                # We normalize each block separately so that Vocals and Drums don't interfere!
                # 98th percentile ensures loud beats hit the top, but silence stays at bottom.
                band_max = np.percentile(S_db, 98, axis=1, keepdims=True)
                
                # Dynamic range: 35 dB difference from silence to peak
                dynamic_range = 35.0
                S_norm = (S_db - (band_max - dynamic_range)) / dynamic_range
                S_norm = np.clip(S_norm, 0.0, 1.0)
                
                # Punchy curve
                S_punchy = np.power(S_norm, 1.5)
                
                # Transpose to (frames, bars)
                S_final = S_punchy.T
                
                self._audio_frames = S_final.tolist()

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
                pos_sec = 0.0
                if self.app and hasattr(self.app, 'player_bar') and self.app.player_bar.engine:
                    pos_sec = self.app.player_bar.engine.get_actual_pos()
                else:
                    pos_sec = pygame.mixer.music.get_pos() / 1000.0
                    
                frame_idx = int(pos_sec * self._fps)

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
                    self._dot_v[i] = -0.8          # gentle upward kick
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
