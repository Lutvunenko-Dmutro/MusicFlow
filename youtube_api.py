import os
import requests
from io import BytesIO
from PIL import Image
import yt_dlp
import customtkinter as ctk

def get_preview_info(url, mode, success_callback, error_callback, image_callback, default_icon_path):
    """
    Отримує інформацію про відео/плейліст та завантажує обкладинку.
    """
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': 'in_playlist'}
        if mode == "Single Track":
            ydl_opts['noplaylist'] = True
        else:
            ydl_opts['noplaylist'] = False
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                error_callback("Video Unavailable / Error", "Cannot fetch info for this link")
                return
        
        title = info.get('title', 'Unknown Title')
        artist = info.get('uploader', 'Unknown Artist')
        thumb_url = info.get('thumbnail')
        
        if info.get('_type') == 'playlist':
            artist = f"Playlist • {info.get('playlist_count', '?')} videos"
            
        success_callback(title, artist)
        
        if thumb_url:
            try:
                response = requests.get(thumb_url, timeout=5)
                if response.status_code == 200:
                    img_data = response.content
                    image = Image.open(BytesIO(img_data))
                    # Crop to square
                    width, height = image.size
                    new_size = min(width, height)
                    left = (width - new_size)/2
                    top = (height - new_size)/2
                    right = (width + new_size)/2
                    bottom = (height + new_size)/2
                    image = image.crop((left, top, right, bottom))
                    
                    photo = ctk.CTkImage(light_image=image, dark_image=image, size=(80, 80))
                    image_callback(photo)
                    return
            except Exception:
                pass
                
        # Fallback placeholder
        if os.path.exists(default_icon_path):
            image = Image.open(default_icon_path)
            photo = ctk.CTkImage(light_image=image, dark_image=image, size=(50, 50))
            image_callback(photo)
            
    except Exception as e:
        error_callback("Ready to download", "Paste a link above")
