import pygame
import os

class PlaybackEngine:
    """Обертка над pygame.mixer для керування відтворенням аудіо"""
    def __init__(self):
        # Ініціалізуємо мікшер, якщо він ще не ініціалізований
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        self.is_playing = False
        self.current_song_path = None
        self.song_length = 0.0
        self.current_pos = 0.0

    def load_song(self, path):
        """Завантажує пісню та обчислює її довжину"""
        if not os.path.exists(path):
            return False
            
        try:
            pygame.mixer.music.load(path)
            self.current_song_path = path
            
            # Отримуємо точну довжину без завантаження всього файлу в RAM!
            self.song_length = 0.0
            try:
                from mutagen.mp3 import MP3
                audio = MP3(path)
                if audio is not None and hasattr(audio.info, 'length'):
                    self.song_length = audio.info.length
            except Exception as e:
                print(f"Mutagen failed to read length: {e}")
                
            self.current_pos = 0.0
            self.is_playing = False # СКИДАЄМО СТАТУС ПРИ ЗАВАНТАЖЕННІ НОВОЇ ПІСНІ!
            self.is_paused = False
            return True
        except Exception as e:
            print(f"Помилка завантаження пісні: {e}")
            return False

    def play(self):
        """Починає або продовжує відтворення"""
        if not self.current_song_path:
            return False
            
        if self.is_playing:
            return True # Вже грає
            
        if getattr(self, 'is_paused', False):
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            pygame.mixer.music.play()
            
        self.is_playing = True
        return True

    def pause(self):
        """Призупиняє відтворення"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True

    def seek(self, pos_seconds):
        """Перемотує пісню на вказану секунду"""
        if not self.current_song_path: return
        
        self.current_pos = pos_seconds
        pygame.mixer.music.play(start=pos_seconds)
        self.is_paused = False
        if not self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True

    def set_volume(self, volume):
        """Встановлює гучність (0.0 - 1.0)"""
        pygame.mixer.music.set_volume(volume)

    def get_actual_pos(self):
        """Отримує точну поточну позицію в секундах"""
        if self.is_playing and pygame.mixer.music.get_busy():
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return self.current_pos + (pos_ms / 1000.0)
        return self.current_pos
