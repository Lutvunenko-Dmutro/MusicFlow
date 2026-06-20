import os
import io
import json
from datetime import datetime
from PIL import Image
try:
    from mutagen.id3 import ID3
except ImportError:
    ID3 = None

import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, "download_history.db")

def _init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            artist TEXT,
            url TEXT,
            filepath TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    return conn

def get_json_history():
    """Load the full persistent download history from SQLite (keeps function name for compatibility)."""
    conn = None
    try:
        conn = _init_db()
        cursor = conn.cursor()
        cursor.execute("SELECT title, artist, url, filepath, timestamp FROM history ORDER BY id DESC")
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "title": row[0],
                "artist": row[1],
                "url": row[2],
                "filepath": row[3],
                "timestamp": row[4]
            })
        return history
    except Exception as e:
        print(f"Error reading DB: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_to_json_history(title, artist, url, filepath):
    """Add a completed download or played song to the SQLite database."""
    conn = None
    try:
        conn = _init_db()
        cursor = conn.cursor()
        
        # Remove old entry for this file if it exists, to move it to the top
        cursor.execute("DELETE FROM history WHERE filepath = ?", (filepath,))
        
        # Insert new entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute('''
            INSERT INTO history (title, artist, url, filepath, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (title or "Unknown Title", artist or "Unknown Artist", url, filepath, timestamp))
        
        # Limit to 200 items
        cursor.execute("SELECT COUNT(*) FROM history")
        count = cursor.fetchone()[0]
        if count > 200:
            # Delete oldest (smallest id)
            cursor.execute("DELETE FROM history WHERE id IN (SELECT id FROM history ORDER BY id ASC LIMIT ?)", (count - 200,))
            
        conn.commit()
    except Exception as e:
        print(f"Error saving to DB: {e}")
    finally:
        if conn:
            conn.close()

def clear_json_history():
    """Clears all history from the database."""
    conn = None
    try:
        conn = _init_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
    except Exception:
        pass
    finally:
        if conn:
            conn.close()

# Alias for settings.py compatibility
clear_history_data = clear_json_history

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
    Deletes the mp3 and associated files (.lrc, .jpg, .webp), and removes it from SQLite history.
    """
    try:
        # 1. Remove from database
        conn = None
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE filepath = ?", (path,))
            conn.commit()
        except Exception:
            pass
        finally:
            if conn:
                conn.close()

        # 2. Delete actual files
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
