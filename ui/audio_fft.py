"""
audio_fft.py — FFT/Librosa аналіз аудіо для AudioVisualizer.
Весь «важкий» розрахунок частот і кешування живе тут.
"""
import os
import hashlib
import numpy as np

# --- Constants ---
SAMPLE_RATE = 44100
FFT_SIZE    = 8192
AGC_ALPHA   = 0.02
AGC_MIN     = 1e-6
ATTACK      = 0.80
RELEASE     = 0.15
GRAVITY     = 0.35


def get_cache_path(filepath, bars):
    """Унікальний шлях кешу для пісні + поточних налаштувань."""
    appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    cache_dir = os.path.join(appdata, "YouTubeMusicPro", "viz_cache")
    os.makedirs(cache_dir, exist_ok=True)
    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    raw_key = f"{filepath}|{file_size}|LIBROSA_SMART_STEMS_V1|{bars}"
    key_hash = hashlib.md5(raw_key.encode()).hexdigest()
    return os.path.join(cache_dir, f"{key_hash}.npy")


def load_from_cache(cache_file):
    """Повертає список фреймів із кешу або None."""
    if not os.path.exists(cache_file):
        return None
    try:
        cached = np.load(cache_file, allow_pickle=False)
        return cached.tolist()
    except Exception as e:
        print(f"[Visualizer] Cache read failed, recomputing: {e}")
        return None


def save_to_cache(cache_file, frames):
    """Зберігає фрейми у кеш."""
    try:
        np.save(cache_file, np.array(frames, dtype=np.float32))
    except Exception as e:
        print(f"[Visualizer] Cache write failed: {e}")


def analyze_audio(filepath, bars, fps):
    """
    Аналізує аудіо файл через librosa + smart stem separation.
    Повертає список фреймів (кожен — список значень 0..1 для кожного бару).
    """
    import librosa
    import scipy.signal

    y, sr = librosa.load(filepath, sr=22050, mono=True)

    # Smart stem separation
    y_perc = librosa.effects.percussive(y, margin=2.0)
    y_harm = librosa.effects.harmonic(y, margin=2.0)

    def lowpass_filter(data, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = scipy.signal.butter(order, normal_cutoff, btype='low', analog=False)
        return scipy.signal.lfilter(b, a, data)

    y_bass = lowpass_filter(y, cutoff=250.0, fs=sr)
    hop_length = int(sr / fps)
    bpb = bars // 5  # bars per block

    # Spectrograms per instrument group
    S_bass   = librosa.feature.melspectrogram(y=y_bass,  sr=sr, n_mels=bpb, fmin=20,   fmax=250,   hop_length=hop_length)
    S_drums  = librosa.feature.melspectrogram(y=y_perc,  sr=sr, n_mels=bpb, fmin=50,   fmax=1000,  hop_length=hop_length)
    S_vocals = librosa.feature.melspectrogram(y=y_harm,  sr=sr, n_mels=bpb, fmin=300,  fmax=3000,  hop_length=hop_length)
    S_melody = librosa.feature.melspectrogram(y=y_harm,  sr=sr, n_mels=bpb, fmin=1500, fmax=6000,  hop_length=hop_length)
    S_cymbal = librosa.feature.melspectrogram(y=y_perc,  sr=sr, n_mels=bpb, fmin=4000, fmax=10000, hop_length=hop_length)

    S_combined = np.vstack([S_bass, S_drums, S_vocals, S_melody, S_cymbal])
    S_db = librosa.power_to_db(S_combined, ref=np.max)

    # Per-band normalisation
    band_max = np.percentile(S_db, 98, axis=1, keepdims=True)
    dynamic_range = 35.0
    S_norm = (S_db - (band_max - dynamic_range)) / dynamic_range
    S_norm = np.clip(S_norm, 0.0, 1.0)
    S_punchy = np.power(S_norm, 1.5)

    return S_punchy.T.tolist()  # (frames, bars)
