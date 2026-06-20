"""
Допоміжні функції для download_engine.py:
- парсинг рядків прогресу yt-dlp
- пост-обробка MP3 (метадані, обкладинка, лірика, історія)
"""
import os
import re


def parse_progress_line(line):
    """Парсить рядок '[download] X%' від yt-dlp. Повертає (percent_float, details_dict) або None."""
    if "[download]" not in line or "%" not in line:
        return None
    try:
        percent_match = re.search(r'(\d+\.\d+)%', line)
        if not percent_match:
            return None
        percent_val = float(percent_match.group(1)) / 100.0

        speed = ""
        eta = ""
        size = ""

        speed_match = re.search(r'at\s+([~0-9a-zA-Z\./]+)', line)
        if speed_match:
            speed = speed_match.group(1).replace('~', '').strip()

        eta_match = re.search(r'ETA\s+([\d:]+)', line)
        if eta_match:
            eta = eta_match.group(1)

        size_match = re.search(r'of\s+~?([0-9a-zA-Z\.]+)', line)
        if size_match:
            size = size_match.group(1).strip()

        details = {
            'percent_str': f"{percent_match.group(1)}%",
            'speed': speed,
            'eta': eta,
            'size': size,
        }
        return percent_val, details
    except Exception:
        return None


def handle_status_line(line, status_callback):
    """Виводить статус на основі спеціальних ключових рядків yt-dlp."""
    if "[ExtractAudio]" in line:
        status_callback("Конвертація у MP3...")
    elif "[SponsorBlock]" in line and "Fetching" in line:
        status_callback("Завантаження сегментів реклами...")
    elif "[ModifyChapters]" in line:
        status_callback("Видалення реклами...")
    elif "[Metadata]" in line:
        status_callback("Збереження обкладинки та тегів...")
    elif "[download] Downloading video" in line:
        status_callback("Завантаження відео...")


def postprocess_single(mp3_filepath, jpg_filepath, raw_title, raw_artist,
                        url, fetch_lyrics, status_callback, progress_callback, success_callback):
    """Пост-обробка одиночного MP3 файлу після завантаження."""
    from utils.metadata_utils import embed_metadata, fetch_lrc
    from core.history_manager import add_to_json_history

    lyrics_text = None
    if fetch_lyrics:
        status_callback("Пошук тексту пісні (LRC)...")
        progress_callback(None, {'indeterminate': True, 'percent_str': 'Search LRC'})
        filename_base = os.path.splitext(mp3_filepath)[0]
        lyrics_text = fetch_lrc(raw_title, raw_artist, filename_base)

    progress_callback(0.95, {'percent_str': 'Embedding'})
    status_callback("Вшивання обкладинки та метаданих...")
    embed_metadata(mp3_filepath, jpg_filepath, raw_title, raw_artist, lyrics_text)

    if os.path.exists(jpg_filepath):
        try:
            os.remove(jpg_filepath)
        except Exception:
            pass

    add_to_json_history(raw_title, raw_artist, url, mp3_filepath)
    success_callback(raw_artist, raw_title, mp3_filepath)


def postprocess_playlist(last_mp3, output_folder, raw_title, raw_artist, url, success_callback):
    """Пост-обробка плейлиста після завантаження."""
    from core.history_manager import add_to_json_history
    add_to_json_history(raw_title or "Playlist", raw_artist or "Various", url, output_folder)
    if last_mp3 and os.path.exists(last_mp3):
        success_callback("Playlist", "Complete", last_mp3)
    else:
        success_callback("Playlist", "Complete", output_folder)
