import os
import json
import shutil
import sys

class I18nManager:
    _instance = None
    
    def __init__(self, config_manager=None):
        self.locales_dir = self._get_locales_dir()
        self.translations = {}
        self.available_langs = {}
        
        self.current_lang = "uk"
        if config_manager:
            self.current_lang = config_manager.get("language", "uk")
            
        self._load_translations()

    @classmethod
    def get_instance(cls, config_manager=None):
        if cls._instance is None:
            cls._instance = cls(config_manager)
        return cls._instance

    def _get_locales_dir(self):
        """Знайде або створить папку з перекладами в LocalAppData."""
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        user_locales_dir = os.path.join(appdata, "YouTubeMusicPro", "locales")
        
        # Завжди копіюємо актуальні файли перекладу з папки програми (щоб оновити кеш, якщо додали нові ключі)
        if not os.path.exists(user_locales_dir):
            os.makedirs(user_locales_dir, exist_ok=True)
            
        # Звідки брати базові файли (при запуску з коду або з exe)
        if hasattr(sys, '_MEIPASS'):
            source_dir = os.path.join(sys._MEIPASS, 'locales')
        else:
            source_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'locales')
            
        if os.path.exists(source_dir):
            for f in os.listdir(source_dir):
                if f.endswith('.json'):
                    shutil.copy2(os.path.join(source_dir, f), os.path.join(user_locales_dir, f))
                        
        return user_locales_dir

    def _load_translations(self):
        """Завантажує всі доступні мови та вибраний переклад."""
        if not os.path.exists(self.locales_dir):
            return
            
        for f in os.listdir(self.locales_dir):
            if f.endswith('.json'):
                lang_code = f.replace('.json', '')
                path = os.path.join(self.locales_dir, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        self.available_langs[lang_code] = data.get("lang_name", lang_code.upper())
                        if lang_code == self.current_lang:
                            self.translations = data
                except Exception as e:
                    print(f"Failed to load locale {f}: {e}")

    def get_text(self, key, default=None):
        """Отримує перекладений текст по ключу."""
        return self.translations.get(key, default if default else key)

def _(key, default=None):
    """Глобальна функція-хелпер для швидкого доступу до перекладу."""
    return I18nManager.get_instance().get_text(key, default)
