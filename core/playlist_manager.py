import os
import random
from core.history_manager import  get_json_history, get_history_items

class PlaylistManager:
    """Менеджер для керування відтворенням, чергою, історією та наступною/попередньою піснею"""
    def __init__(self, player_bar, output_folder):
        self.player_bar = player_bar
        self.output_folder = output_folder
        self.last_downloaded_file = None

    def play_initial(self):
        """Логіка натискання кнопки Play, коли плеєр порожній"""
        if self.last_downloaded_file and os.path.exists(self.last_downloaded_file):
            self.player_bar.play_specific_music(self.last_downloaded_file)
            return
            
        # 1. Спробувати взяти останню прослухану пісню зі збереженої історії
        json_history = get_json_history()
        if json_history:
            last_played_path = json_history[0].get("filepath")
            if last_played_path and os.path.exists(last_played_path):
                self.last_downloaded_file = last_played_path
                self.player_bar.play_specific_music(self.last_downloaded_file)
                return

        # 2. Якщо історії ще немає, беремо найновіший файл із папки
        placeholder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "music_placeholder.png")
        items = get_history_items(self.output_folder, 1, placeholder)
        if items and os.path.exists(items[0]['path']):
            self.last_downloaded_file = items[0]['path']
            self.player_bar.play_specific_music(self.last_downloaded_file)
        else:
            if hasattr(self.player_bar.app, 'update_status'):
                self.player_bar.app.update_status("⚠️ Спочатку завантажте пісню, щоб її прослухати!")

    def play_next(self):
        self._switch_song(direction=1)

    def play_prev(self):
        self._switch_song(direction=-1)

    def _switch_song(self, direction=1):
        if not self.player_bar.engine.current_song_path: return
        
        placeholder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "music_placeholder.png")
        items = get_history_items(self.output_folder, 1000, placeholder)
        if not items: return
        
        current_norm = os.path.normcase(os.path.abspath(self.player_bar.engine.current_song_path))
        current_idx = -1
        for i, item in enumerate(items):
            if os.path.normcase(os.path.abspath(item['path'])) == current_norm:
                current_idx = i
                break
                
        if current_idx != -1:
            if self.player_bar.shuffle_enabled:
                if len(items) > 1:
                    next_idx = current_idx
                    while next_idx == current_idx:
                        next_idx = random.randint(0, len(items) - 1)
                else:
                    next_idx = 0
            else:
                next_idx = current_idx + direction
                if next_idx >= len(items) or next_idx < 0:
                    if self.player_bar.repeat_mode == 1:
                        next_idx = next_idx % len(items)
                    else:
                        return # End of playlist

            self.player_bar.play_specific_music(items[next_idx]['path'])
