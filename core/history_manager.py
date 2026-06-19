import os
import io
import json
from datetime import datetime
from PIL import Image
try:
    from mutagen.id3 import ID3
except ImportError:
    ID3 = None

HISTORY_JSON_FILE = "download_history.json"

def get_json_history():
    """Load the full persistent download history from JSON."""
    if not os.path.exists(HISTORY_JSON_FILE):
        return []
    try:
        with open(HISTORY_JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def add_to_json_history(title, artist, url, filepath):
    """Add a completed download or played song to the persistent JSON history."""
    history = get_json_history()
    
    # Видалити старий запис, якщо такий файл вже є в історії, щоб підняти його наверх
    history = [item for item in history if item.get("filepath") != filepath]
    
    entry = {
        "title": title or "Unknown Title",
        "artist": artist or "Unknown Artist",
        "url": url,
        "filepath": filepath,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    history.insert(0, entry) # add to top
    history = history[:200]  # limit to 200 items
    
    try:
        with open(HISTORY_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def clear_json_history():
    try:
        if os.path.exists(HISTORY_JSON_FILE):
            os.remove(HISTORY_JSON_FILE)
    except Exception:
        pass

def get_history_items(output_folder, max_items=10, default_icon_path=None):
    """
    Returns a list of history items (dicts) containing metadata and cover image.
    """
    items = []
    if not os.path.exists(output_folder):
        return items
        
    try:
        files = [f for f in os.listdir(output_folder) if f.endswith(".mp3")]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(output_folder, x)), reverse=True)
        
        default_image = None
        if default_icon_path and os.path.exists(default_icon_path):
            default_image = Image.open(default_icon_path)
            
        for f in files[:max_items]:
            f_path = os.path.join(output_folder, f)
            size_mb = os.path.getsize(f_path) / (1024 * 1024)
            
            cover_img = None
            if ID3 is not None:
                try:
                    audio = ID3(f_path)
                    for tag in audio.values():
                        if tag.FrameID == 'APIC':
                            cover_img = Image.open(io.BytesIO(tag.data))
                            break
                except Exception:
                    pass
            
            if cover_img is None and default_image is not None:
                cover_img = default_image.copy()
                
            if cover_img:
                width, height = cover_img.size
                new_size = min(width, height)
                left = (width - new_size)/2
                top = (height - new_size)/2
                right = (width + new_size)/2
                bottom = (height + new_size)/2
                cover_img = cover_img.crop((left, top, right, bottom)).resize((36, 36))
                
            items.append({
                'filename': f,
                'path': f_path,
                'size_mb': size_mb,
                'cover_img': cover_img
            })
    except Exception:
        pass
        
    return items

def delete_history_files(path):
    """
    Deletes the mp3 and associated files (.lrc, .jpg, .webp).
    """
    try:
        if os.path.exists(path):
            os.remove(path)
            
        base_path = os.path.splitext(path)[0]
        for ext in ['.lrc', '.jpg', '.webp']:
            associated_file = base_path + ext
            if os.path.exists(associated_file):
                try:
                    os.remove(associated_file)
                except Exception:
                    pass
    except Exception as e:
        raise Exception(f"Failed to delete {os.path.basename(path)}: {e}")
