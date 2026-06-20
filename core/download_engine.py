import os
import re
import json
import subprocess

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    ffmpeg_exe = "ffmpeg"
except ImportError:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

from core.ytdlp_manager import ensure_ytdlp_exists, update_ytdlp, get_ytdlp_path
from core.download_helpers import parse_progress_line, handle_status_line, postprocess_single, postprocess_playlist


def download_and_process_music(url, output_folder, mode, fetch_lyrics,
                                status_callback, progress_callback,
                                success_callback, error_callback,
                                set_process_cb=None, qual="320", use_sponsorblock=True):
    """Основний двигун для завантаження музики через yt-dlp.exe."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        def _attempt_download(force_update):
            ensure_ytdlp_exists(status_callback)
            update_ytdlp(status_callback, force=force_update)
            ytdlp_exe = get_ytdlp_path()

            is_playlist = (mode == "Full Playlist")
            raw_title, raw_artist = "Playlist", "YouTube"
            filename_base = None
            last_downloaded_mp3 = None
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            if not is_playlist:
                status_callback("🔍 Отримання інформації про відео...")
                info_cmd = [
                    ytdlp_exe, "--dump-json", "--windows-filenames",
                    "-o", os.path.join(output_folder, "%(title)s.%(ext)s"),
                    "--no-warnings", "--no-playlist", url
                ]
                result = subprocess.run(info_cmd, capture_output=True, text=True,
                                        encoding="utf-8", creationflags=creationflags)
                if result.returncode != 0:
                    raise Exception(f"Не вдалося отримати доступ.\nДеталі: {result.stderr.strip()}")

                info = json.loads(result.stdout.strip().split('\n')[-1])
                raw_title = info.get('title', 'Unknown Title')
                raw_artist = info.get('uploader', 'Unknown Artist').replace(' - Topic', '')
                filename_base = os.path.splitext(info.get('_filename'))[0]

            cmd = _build_download_cmd(ytdlp_exe, output_folder, qual, use_sponsorblock, is_playlist, url)

            if not is_playlist:
                status_callback(f"Завантаження: {raw_artist} - {raw_title}...")
            else:
                status_callback("Завантаження плейліста (може зайняти час)...")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding="utf-8", creationflags=creationflags)
            if set_process_cb:
                set_process_cb(process)

            error_log = []
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                print(f"[yt-dlp] {line}")
                if "ERROR:" in line or "error" in line.lower():
                    error_log.append(line)

                handle_status_line(line, status_callback)

                if "[ExtractAudio] Destination:" in line:
                    match = re.search(r'\[ExtractAudio\] Destination: (.*\.mp3)', line)
                    if match:
                        last_downloaded_mp3 = match.group(1).strip()
                        if is_playlist:
                            progress_callback(None, {'item_finished': True})

                parsed = parse_progress_line(line)
                if parsed:
                    percent_val, details = parsed
                    progress_callback(percent_val * 0.8 if not is_playlist else percent_val, details)
                    if not is_playlist:
                        status_callback("Завантаження музики...")

            process.wait()
            if process.returncode != 0:
                err_msg = "\n".join(error_log[-3:]) if error_log else "Невідома помилка yt-dlp"
                raise Exception(f"Помилка під час завантаження: {err_msg}")

            if not is_playlist and filename_base:
                postprocess_single(
                    filename_base + ".mp3", filename_base + ".jpg",
                    raw_title, raw_artist, url,
                    fetch_lyrics, status_callback, progress_callback, success_callback
                )
            else:
                postprocess_playlist(last_downloaded_mp3, output_folder,
                                     raw_title, raw_artist, url, success_callback)

        try:
            _attempt_download(force_update=False)
        except Exception:
            status_callback("⚠️ Спроба авто-лікування (оновлення yt-dlp)...")
            _attempt_download(force_update=True)

    except Exception as e:
        import traceback
        print("====== КРИТИЧНА ПОМИЛКА ЗАВАНТАЖЕННЯ ======")
        traceback.print_exc()
        print("===========================================")
        error_callback(str(e))


def _build_download_cmd(ytdlp_exe, output_folder, qual, use_sponsorblock, is_playlist, url):
    """Будує список аргументів команди yt-dlp."""
    cmd = [
        ytdlp_exe,
        "--format", "bestaudio/best",
        "--extract-audio", "--audio-format", "mp3",
        "--audio-quality", qual,
        "--embed-metadata", "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "--windows-filenames", "--no-warnings", "--newline",
        "-o", os.path.join(output_folder, "%(title)s.%(ext)s"),
    ]
    if use_sponsorblock:
        cmd.insert(cmd.index("--embed-metadata"), "--sponsorblock-remove")
        cmd.insert(cmd.index("--embed-metadata"), "sponsor,intro,outro,music_offtopic")
    cmd.append("--no-playlist" if not is_playlist else "--yes-playlist")
    cmd.append(url)
    return cmd
