"""
player_bar_logic.py — логіка відтворення для PlayerBarFrame.
"""
import os
from PIL import Image
import customtkinter as ctk


def load_and_play(bar, path):
    """Завантажує та починає відтворення пісні."""
    if not os.path.exists(path):
        return

    bar.current_song_path = path
    bar.current_lyrics_lines = []
    if hasattr(bar, 'mini_lyrics_lbl'):
        bar.mini_lyrics_lbl.configure(text="")

    if not bar.engine.load_song(path):
        return

    try:
        bar.visualizer.load_song(path)
        bar.engine.play()
        bar.btn_play_pause.configure(image=bar.icon_pause)
        bar.visualizer.start()
        bar.time_total_lbl.configure(text=bar.format_time(bar.engine.song_length))

        from utils.metadata_utils import extract_track_metadata, parse_lrc_text
        metadata  = extract_track_metadata(path)
        title     = metadata.get('title')
        artist    = metadata.get('artist')
        cover_img = metadata.get('cover_img')

        lyrics_text = metadata.get('lyrics_text')
        if lyrics_text:
            bar.current_lyrics_lines = parse_lrc_text(lyrics_text)

        if cover_img is None and bar.default_cover is not None:
            cover_img = bar.default_cover.copy()

        if cover_img:
            w, h = cover_img.size
            sz = min(w, h)
            cover_img = cover_img.crop(((w - sz) // 2, (h - sz) // 2,
                                        (w + sz) // 2, (h + sz) // 2))
            cover_img = cover_img.resize((48, 48), Image.LANCZOS)
            photo = ctk.CTkImage(light_image=cover_img, dark_image=cover_img, size=(48, 48))
            bar.photo = photo
            bar.cover_lbl.configure(image=photo, text="")

        filename = os.path.basename(path)
        display_title = title if title else filename
        if len(display_title) > 30:
            display_title = display_title[:29] + "…"
            
        display_artist = artist if artist else "Playing from library"
        if len(display_artist) > 35:
            display_artist = display_artist[:34] + "…"
            
        bar.title_lbl.configure(text=display_title)
        bar.artist_lbl.configure(text=display_artist)

        try:
            from core.history_manager import add_to_json_history
            add_to_json_history(title if title else filename, artist if artist else "Playing from library", "", path)
            if hasattr(bar.app, 'history_area') and bar.app.history_area.winfo_manager():
                bar.app.history_area.load_history()
        except Exception as e:
            print(f"Failed to update history: {e}")

    except Exception as e:
        print(f"Error playing {path}: {e}")


def toggle_play(bar):
    """Play / Pause. Якщо нічого не завантажено — грає останню з історії."""
    if not bar.engine.current_song_path:
        try:
            from core.history_manager import get_json_history
            for item in get_json_history():
                path = item.get('filepath')
                if path and os.path.exists(path):
                    bar.play_specific_music(path)
                    return
        except Exception as e:
            print(f"Failed to load from history: {e}")
        return

    if bar.engine.is_playing:
        bar.engine.pause()
        bar.btn_play_pause.configure(image=bar.icon_play)
        if hasattr(bar, 'visualizer'):
            bar.visualizer.stop()
    else:
        bar.engine.play()
        bar.btn_play_pause.configure(image=bar.icon_pause)
        if hasattr(bar, 'visualizer'):
            bar.visualizer.start()


def stop_music(bar):
    bar.engine.pause()
    bar.engine.current_pos = 0.0
    bar.engine.is_playing  = False
    bar.btn_play_pause.configure(image=bar.icon_play)
    bar.progress_slider.set(0)
    bar.time_current_lbl.configure(text="0:00")
    if hasattr(bar, 'visualizer'):
        bar.visualizer.stop()



def seek(bar, value):
    if not bar.engine.current_song_path:
        return
    bar.is_seeking = True
    if bar.seek_timer:
        bar.after_cancel(bar.seek_timer)
    bar.seek_timer = bar.after(200, lambda v=value: perform_seek(bar, v))


def perform_seek(bar, value):
    if not bar.engine.current_song_path:
        return
    bar.is_seeking = False
    pos = (float(value) / 100) * bar.engine.song_length
    bar.engine.seek(pos)


def toggle_shuffle(bar):
    bar.shuffle_enabled = not bar.shuffle_enabled
    bar.btn_shuffle.configure(
        image=bar.icon_shuffle_act if bar.shuffle_enabled else bar.icon_shuffle, text=""
    )


def toggle_repeat(bar):
    bar.repeat_mode = (bar.repeat_mode + 1) % 3
    icons = {0: bar.icon_repeat, 1: bar.icon_repeat_act, 2: bar.icon_repeat_one_act}
    bar.btn_repeat.configure(image=icons[bar.repeat_mode], text="")


def show_lyrics(bar):
    if not bar.current_song_path:
        return
    lyrics = None
    try:
        from mutagen.id3 import ID3
        if ID3 is not None:
            tags = ID3(bar.current_song_path)
            for key, tag in tags.items():
                if key.startswith('USLT'):
                    lyrics = tag.text
                    break
    except Exception:
        pass
    display_lyrics_window(bar, lyrics)


def display_lyrics_window(bar, lyrics):
    from ui.lyrics_karaoke import KaraokeLyricsUI

    def on_generate():
        from core.ai_lyrics import is_model_installed, transcribe_audio_ui
        if not is_model_installed():
            ask_install_model(bar)
        else:
            transcribe_audio_ui(bar.app, bar.current_song_path,
                                on_success=lambda lyr: display_lyrics_window(bar, lyr))

    bar.lyrics_ui = KaraokeLyricsUI(bar.app, lyrics, on_regenerate=on_generate)


def ask_install_model(bar):
    import customtkinter as ctk
    dialog = ctk.CTkToplevel(bar.app)
    dialog.title("ШІ Модель відсутня")
    dialog.geometry("420x180")
    dialog.attributes('-topmost', True)
    dialog.grab_set()
    dialog.resizable(False, False)
    dialog.update_idletasks()
    x = bar.app.winfo_x() + (bar.app.winfo_width()  - 420) // 2
    y = bar.app.winfo_y() + (bar.app.winfo_height() - 180) // 2
    dialog.geometry(f"+{x}+{y}")

    ctk.CTkLabel(dialog,
                 text="Для генерації тексту пісень потрібна AI модель.\n"
                      "Бажаєте завантажити її зараз (~250 МБ)?\n"
                      "Це потрібно зробити лише один раз.",
                 font=ctk.CTkFont(size=14)).pack(pady=20)

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=10)

    def on_yes():
        dialog.destroy()
        from core.ai_lyrics import download_ai_model_ui, transcribe_audio_ui
        download_ai_model_ui(
            bar.app,
            on_complete=lambda: transcribe_audio_ui(
                bar.app, bar.current_song_path,
                on_success=lambda lyr: display_lyrics_window(bar, lyr)
            )
        )

    ctk.CTkButton(btn_frame, text="Так, завантажити",
                  fg_color="#E52D27", hover_color="#c0241f",
                  command=on_yes).pack(side="left", expand=True, padx=10)
    ctk.CTkButton(btn_frame, text="Ні",
                  fg_color=("#D1D5DB", "#333333"), hover_color=("#9CA3AF", "#4b5563"),
                  text_color=("#111827", "#ffffff"),
                  command=dialog.destroy).pack(side="right", expand=True, padx=10)
