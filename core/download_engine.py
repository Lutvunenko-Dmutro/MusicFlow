import os
import re
import json
import subprocess

try:
    # static-ffmpeg містить і ffmpeg, і ffprobe
    import static_ffmpeg
    static_ffmpeg.add_paths()
    ffmpeg_exe = "ffmpeg"
except ImportError:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
from core.ytdlp_manager import  ensure_ytdlp_exists, update_ytdlp, get_ytdlp_path
from utils.metadata_utils import  embed_metadata, fetch_lrc

def download_and_process_music(url, output_folder, mode, fetch_lyrics, status_callback, progress_callback, success_callback, error_callback, set_process_cb=None, qual="320", use_sponsorblock=True):
    """
    Основний двигун для завантаження музики через yt-dlp.exe.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        def _attempt_download(force_update):
            # 1. Завантажуємо і оновлюємо yt-dlp.exe
            ensure_ytdlp_exists(status_callback)
            update_ytdlp(status_callback, force=force_update)
            
            ytdlp_exe = get_ytdlp_path()

            is_playlist = (mode == "Full Playlist")
            
            raw_title = "Playlist"
            raw_artist = "YouTube"
            filename_base = None
            last_downloaded_mp3 = None
            
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            if not is_playlist:
                status_callback("🔍 Отримання інформації про відео...")
                info_cmd = [
                    ytdlp_exe, 
                    "--dump-json", 
                    "--windows-filenames", 
                    "-o", os.path.join(output_folder, "%(title)s.%(ext)s"), 
                    "--no-warnings",
                    "--no-playlist",
                    url
                ]
                
                result = subprocess.run(info_cmd, capture_output=True, text=True, encoding="utf-8", creationflags=creationflags)
                if result.returncode != 0:
                    raise Exception(f"Не вдалося отримати доступ. Можливо потрібна авторизація.\nДеталі: {result.stderr.strip()}")
                    
                info = json.loads(result.stdout.strip().split('\n')[-1])
                raw_title = info.get('title', 'Unknown Title')
                uploader = info.get('uploader', 'Unknown Artist')
                raw_artist = uploader.replace(' - Topic', '')
                
                filename_base = os.path.splitext(info.get('_filename'))[0]

            # 3. Виконуємо безпосередньо завантаження
            cmd = [
                ytdlp_exe,
                "--format", "bestaudio/best",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", qual,
                "--embed-metadata",
                "--write-thumbnail",
                "--convert-thumbnails", "jpg",
                "--windows-filenames",
                "--no-warnings",
                "--newline",
                "-o", os.path.join(output_folder, "%(title)s.%(ext)s")
            ]
            
            if use_sponsorblock:
                cmd.insert(cmd.index("--embed-metadata"), "--sponsorblock-remove")
                cmd.insert(cmd.index("--embed-metadata"), "sponsor,intro,outro,music_offtopic")
            
            if not is_playlist:
                cmd.append("--no-playlist")
            else:
                cmd.append("--yes-playlist")
                
            cmd.append(url)

            if not is_playlist:
                status_callback(f"Завантаження: {raw_artist} - {raw_title}...")
            else:
                status_callback("Завантаження плейліста (може зайняти час)...")
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", creationflags=creationflags)
            
            if set_process_cb:
                set_process_cb(process)
            
            # 4. Читаємо вивід yt-dlp в реальному часі для смуги прогресу
            error_log = []
            for line in process.stdout:
                line = line.strip()
                if line:
                    print(f"[yt-dlp] {line}") # ДРУКУЄМО ВСЕ В КОНСОЛЬ
                    if "ERROR:" in line or "error" in line.lower():
                        error_log.append(line)
                        
                if "[ExtractAudio]" in line:
                    status_callback("🎵 Конвертація у MP3...")
                elif "[SponsorBlock]" in line and "Fetching" in line:
                    status_callback("✂️ Завантаження сегментів реклами...")
                elif "[ModifyChapters]" in line:
                    status_callback("✂️ Видалення реклами...")
                elif "[Metadata]" in line:
                    status_callback("🏷️ Збереження обкладинки та тегів...")
                    
                if "[ExtractAudio] Destination:" in line:
                    match = re.search(r'\[ExtractAudio\] Destination: (.*\.mp3)', line)
                    if match:
                        last_downloaded_mp3 = match.group(1).strip()
                        if is_playlist:
                            progress_callback(None, {'item_finished': True})
                        
                if "[download] Downloading video" in line:
                    status_callback("⬇️ Завантаження відео...")
                    
                if "[download]" in line and "%" in line:
                    try:
                        percent_match = re.search(r'(\d+\.\d+)%', line)
                        if percent_match:
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
                                'size': size
                            }
                            
                            progress_callback(percent_val * 0.8 if not is_playlist else percent_val, details)
                            
                            if not is_playlist:
                                status_callback("Завантаження музики...")
                    except Exception:
                        pass

            process.wait()
            
            if process.returncode != 0:
                err_msg = "\n".join(error_log[-3:]) if error_log else "Невідома помилка yt-dlp"
                print(f"yt-dlp error code {process.returncode}. Log: {err_msg}")
                raise Exception(f"Помилка під час завантаження: {err_msg}")

            if not is_playlist and filename_base:
                mp3_filepath = filename_base + ".mp3"
                jpg_filepath = filename_base + ".jpg"

                # 5. Пошук тексту та вшивання
                lyrics_text = None
                if fetch_lyrics:
                    status_callback("🔍 Пошук тексту пісні (LRC)...")
                    progress_callback(None, {'indeterminate': True, 'percent_str': 'Search LRC'})
                    lyrics_text = fetch_lrc(raw_title, raw_artist, filename_base)
                
                progress_callback(0.95, {'percent_str': 'Embedding'})
                status_callback("💿 Вшивання обкладинки та метаданих...")
                embed_metadata(mp3_filepath, jpg_filepath, raw_title, raw_artist, lyrics_text)
                
                if os.path.exists(jpg_filepath):
                    try:
                        os.remove(jpg_filepath)
                    except Exception:
                        pass
                
                # Save to history log
                from core.history_manager import add_to_json_history
                add_to_json_history(raw_title, raw_artist, url, mp3_filepath)
                
                success_callback(raw_artist, raw_title, mp3_filepath)
            else:
                # Для плейліста повертаємо останній скачаний файл (якщо є)
                from core.history_manager import add_to_json_history
                add_to_json_history(raw_title or "Playlist", raw_artist or "Various", url, output_folder)
                
                if last_downloaded_mp3 and os.path.exists(last_downloaded_mp3):
                    success_callback("Playlist", "Complete", last_downloaded_mp3)
                else:
                    success_callback("Playlist", "Complete", output_folder)

        # Виклик спроб
        try:
            _attempt_download(force_update=False)
        except Exception as e:
            err_str = str(e).lower()
            status_callback("⚠️ Спроба авто-лікування (оновлення yt-dlp)...")
            # Якщо виникла помилка, пробуємо ще раз із примусовим оновленням
            _attempt_download(force_update=True)

    except Exception as e:
        import traceback
        print("====== КРИТИЧНА ПОМИЛКА ЗАВАНТАЖЕННЯ ======")
        traceback.print_exc()
        print("===========================================")
        error_callback(str(e))
