import librosa
import numpy as np

filepath = "My_Music/A Dance With The Laughing Storm ｜ A Knight of The Seven Kingdoms.mp3"

try:
    print(f"Loading {filepath}...")
    y, sr = librosa.load(filepath, sr=22050, mono=True)
    fps = 60
    hop_length = int(sr / fps)
    
    print("Extracting percussive elements...")
    y_perc = librosa.effects.percussive(y, margin=2.0)
    y_boosted = y + (y_perc * 1.5)
    
    print("Generating Melspectrogram...")
    bars = 60
    S = librosa.feature.melspectrogram(y=y_boosted, sr=sr, n_mels=bars, 
                                       n_fft=2048, hop_length=hop_length, 
                                       fmin=20, fmax=8000)
    
    S_db = librosa.power_to_db(S, ref=np.max)
    
    # Use 95th percentile instead of absolute max!
    # This means the top 5% loudest moments will hit the ceiling, making it jump much more often.
    band_max = np.percentile(S_db, 98, axis=1, keepdims=True)
    dynamic_range = 35.0
    S_norm = (S_db - (band_max - dynamic_range)) / dynamic_range
    S_norm = np.clip(S_norm, 0.0, 1.0)
    
    S_punchy = np.power(S_norm, 1.5)
    
    # Analyze the 5 blocks
    num_blocks = 5
    group_size = bars // num_blocks
    
    for b in range(num_blocks):
        start_idx = b * group_size
        end_idx = start_idx + group_size
        block_data = S_punchy[start_idx:end_idx, :]
        
        # Calculate how often the block exceeds certain thresholds
        mean_val = np.mean(block_data)
        peak_val = np.max(block_data)
        hits_over_0_8 = np.mean(block_data > 0.8) * 100
        hits_over_0_5 = np.mean(block_data > 0.5) * 100
        hits_under_0_1 = np.mean(block_data < 0.1) * 100
        
        print(f"Block {b+1} (Bars {start_idx}-{end_idx-1}):")
        print(f"  Mean: {mean_val:.3f}, Peak: {peak_val:.3f}")
        print(f"  % Time > 80% (Big hits): {hits_over_0_8:.2f}%")
        print(f"  % Time > 50% (Medium hits): {hits_over_0_5:.2f}%")
        print(f"  % Time < 10% (Silence/Low): {hits_under_0_1:.2f}%")

except Exception as e:
    print("Error:", e)
