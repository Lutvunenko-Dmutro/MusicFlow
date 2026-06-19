import requests
import os
import re
import sys
from mutagen.mp3 import MP3
# 🔥 Додали USLT для тексту
from mutagen.id3 import ID3, APIC, USLT, error, TIT2, TPE1, TALB

def clean_text(text):
    """Очищає назву від дужок [], (), та зайвих символів після | """
    if not text: return ""
    clean = re.sub(r'[\(\[].*?[\)\]]', '', str(text))
    clean = clean.split('|')[0]
    if ' - ' in clean:
        clean = clean.split(' - ')[0]
    return clean.strip()

def embed_metadata(mp3_path, jpg_path, title, artist, lyrics):
    """Надійно вшиває обкладинку, Назву, Артиста, Альбом та ТЕКСТ для телефонів"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass
            
        # 1. Прописуємо текстові метадані (щоб телефон правильно сортував музику)
        audio.tags.add(TIT2(encoding=3, text=title))       # Назва пісні
        audio.tags.add(TPE1(encoding=3, text=artist))      # Артист
        audio.tags.add(TALB(encoding=3, text=title))       # Альбом 
        
        # 2. Вшиваємо текст, якщо він є
        if lyrics:
            # USLT = Unsynchronized Lyric/Text Transcription
            audio.tags.add(USLT(encoding=3, lang='eng', desc='desc', text=lyrics))
            
        # 3. Вшиваємо обкладинку, якщо вона завантажилась
        if jpg_path and os.path.exists(jpg_path):
            with open(jpg_path, 'rb') as img_file:
                audio.tags.add(
                    APIC(
                        encoding=3,         
                        mime='image/jpeg',  
                        type=3,             # 3 = Обкладинка альбому (Front Cover)
                        desc='Cover',
                        data=img_file.read()
                    )
                )
                
        # Зберігаємо в найстабільнішому для мобільних пристроїв форматі ID3v2.3
        audio.save(v2_version=3)
        
        if lyrics:
            print("🖼 Обкладинка, теги та ТЕКСТ надійно вшиті!")
        else:
            print("🖼 Обкладинка та теги надійно вшиті (тексту немає).")
            
    except Exception as e:
        print(f"⚠️ Не вдалося вшити метадані: {e}")

def fetch_lrc(track_name, artist_name, filename_base):
    """Шукає LRC текст і повертає текст З ТАЙМІНГАМИ для вшивання в MP3"""
    clean_title = clean_text(track_name)
    clean_artist = clean_text(artist_name)
    print(f"🔍 Шукаю текст: '{clean_title}'")
    url = "https://lrclib.net/api/search"
    search_queries = [f"{clean_title} {clean_artist}".strip(), clean_title]
    
    for query in search_queries:
        if not query: continue
        try:
            params = {'q': query}
            response = requests.get(url, params=params)
            if response.status_code == 200 and response.json():
                for result in response.json():
                    synced = result.get('syncedLyrics')
                    
                    if synced:
                        # 🔥 ГОЛОВНА ЗМІНА: Тепер ми повертаємо текст ІЗ ТАЙМІНГАМИ для вшивання!
                        return synced 
        except Exception:
            pass
    return None

def extract_track_metadata(filepath):
    """Витягує назву, артиста, обкладинку та текст з MP3-файлу"""
    metadata = {
        'title': None,
        'artist': None,
        'cover_img': None,
        'lyrics_text': None
    }
    try:
        from mutagen.id3 import ID3
        import io
        from PIL import Image
        
        tags = ID3(filepath)
        
        # Обкладинка
        for tag in tags.values():
            if tag.FrameID == 'APIC':
                metadata['cover_img'] = Image.open(io.BytesIO(tag.data))
                break
                
        # Текст
        if 'TIT2' in tags:
            metadata['title'] = tags['TIT2'].text[0]
        if 'TPE1' in tags:
            metadata['artist'] = tags['TPE1'].text[0]
            
        # Караоке
        for key, tag in tags.items():
            if key.startswith('USLT'):
                metadata['lyrics_text'] = tag.text
                break
                
    except Exception as e:
        print(f"Error reading metadata for {filepath}: {e}")
        
    return metadata

def parse_lrc_text(lyrics_text):
    """Парсить текст у форматі LRC і повертає список (таймкод, рядок)"""
    if not lyrics_text:
        return []
        
    import re
    raw_lines = lyrics_text.split('\n')
    parsed_lines = []
    
    for line in raw_lines:
        line = line.strip()
        match = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)', line)
        if match:
            m = int(match.group(1))
            s = float(match.group(2))
            time_sec = m * 60 + s
            content = match.group(3)
            parsed_lines.append((time_sec, content))
            
    return parsed_lines